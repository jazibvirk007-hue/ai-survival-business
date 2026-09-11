from cortex_voice_command import voice_endpoint_contract


def test_voice_endpoint_contract_is_bounded_and_guarded():
    contract = voice_endpoint_contract()
    assert contract["version"] == "12.0"
    assert contract["max_transcript_chars"] == 4000
    assert contract["financial_actions"] == "blocked-by-default"
    assert contract["external_actions"] == "approval-gated"
    assert "credentials" in contract
