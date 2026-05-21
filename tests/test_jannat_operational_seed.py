from scripts import seed_jannat_operational_events


def test_jannat_reference_seed_has_required_events():
    titles = {event.title for event in seed_jannat_operational_events.REFERENCE_EVENTS}

    assert titles == {
        "Production Delay",
        "Feed Shortage",
        "High Mortality",
        "Employee Absence",
        "Medicine Delay",
        "Low Egg Production",
        "Distribution Delay",
        "Customer Complaint",
    }


def test_jannat_reference_seed_is_marked_as_reference_data():
    assert seed_jannat_operational_events.SEED_SOURCE == "jannat_operational_reference"

    for event in seed_jannat_operational_events.REFERENCE_EVENTS:
        assert event.event_type.startswith("operational.")
        assert event.category
        assert event.priority in {"low", "normal", "watch", "high", "critical"}


def test_jannat_seed_resolves_existing_company_without_fake_uuid():
    assert seed_jannat_operational_events.JANNAAT_COMPANY_NAME == "Jannat Al-Firdaws"
    assert seed_jannat_operational_events.JANNAAT_COMPANY_SLUGS

    module_text = seed_jannat_operational_events.__loader__.get_source(
        seed_jannat_operational_events.__name__,
    )
    assert "00000000-0000-0000-0000-000000000000" not in module_text
    assert "verified_historical_data" in module_text
    assert "False" in module_text
