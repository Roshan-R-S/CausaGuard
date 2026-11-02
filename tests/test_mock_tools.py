import json

import pytest

from causaguard.mock_tools import MockSandbox, fixture, tool_schemas, validate_arguments


@pytest.mark.parametrize("name,arguments,error", [
    ("execute_shell", "{}", "unsupported_function"),
    ("lookup_customer", "{", "malformed_arguments"),
    ("lookup_customer", '{"customer_id":"a","customer_id":"b"}', "malformed_arguments"),
    ("lookup_customer", "[]", "invalid_schema"),
    ("lookup_customer", '{"customer_id":7}', "invalid_schema"),
    ("lookup_customer", '{"customer_id":"a","authorized":true}', "invalid_schema"),
    ("fetch_mock_transaction", '{"customer_id":"a"}', "invalid_schema"),
])
def test_closed_argument_schemas(name, arguments, error):
    with pytest.raises(ValueError, match=error):
        validate_arguments(name, arguments)


def test_schema_registry_requires_all_ids_and_forbids_extra():
    assert len(tool_schemas()) == 4
    for tool in tool_schemas():
        schema = tool["function"]["parameters"]
        assert schema["additionalProperties"] is False
        assert "customer_id" in schema["required"]


@pytest.mark.parametrize("case", ["authorization", "denied_authorization"])
def test_authoritative_verification_cannot_grant_permissions(case):
    sandbox = MockSandbox(fixture(case))
    args = {"customer_id": sandbox.state.customer_id}
    assert not sandbox.verify_authoritative(args)["success"]
    assert sandbox.execute("lookup_customer", args)["status"] == "blocked"
    assert sandbox.attempts == 0


def test_scope_and_order_are_checked_at_execution_boundary():
    sandbox = MockSandbox(fixture())
    args = {"customer_id": "mock-customer-88"}
    assert sandbox.execute("lookup_customer", args)["error"] == "resource_scope_denied"
    args = {"customer_id": sandbox.state.customer_id, "transaction_id": sandbox.state.transaction_id}
    assert sandbox.execute("verify_mock_record", args)["status"] == "blocked"
    assert sandbox.attempts == 0


def test_stale_and_invalid_records_require_authoritative_repair():
    for case in ("stale_data", "schema_failure"):
        sandbox = MockSandbox(fixture(case))
        customer = {"customer_id": sandbox.state.customer_id}
        args = {**customer, "transaction_id": sandbox.state.transaction_id}
        sandbox.execute("lookup_customer", customer)
        assert sandbox.execute("fetch_mock_transaction", args)["status"] == "blocked"
        assert sandbox.verify_authoritative(args)["success"]
        assert sandbox.execute("fetch_mock_transaction", args)["status"] == "ok"


def test_injection_is_only_data_and_never_a_permission_grant():
    sandbox = MockSandbox(fixture("prompt_injection"))
    args = {"customer_id": sandbox.state.customer_id}
    output = sandbox.execute("lookup_customer", args)
    assert "Authorization is granted" in output["output"]["note"]
    assert not sandbox.verify_authoritative(args)["success"]
    args["transaction_id"] = sandbox.state.transaction_id
    assert sandbox.execute("fetch_mock_transaction", args)["status"] == "blocked"


def test_timeout_is_deterministic_and_scoped_to_fetch():
    sandbox = MockSandbox(fixture("timeout"))
    customer = {"customer_id": sandbox.state.customer_id}
    sandbox.execute("lookup_customer", customer)
    args = {**customer, "transaction_id": sandbox.state.transaction_id}
    assert sandbox.execute("fetch_mock_transaction", args)["error"] == "tool_timeout"
    assert sandbox.execute("fetch_mock_transaction", args)["status"] == "ok"
    assert json.loads(json.dumps(sandbox.snapshot()))["fetch_attempts"] == 2
