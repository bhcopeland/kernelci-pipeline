import hw_reg_checker


def make_data(**sections):
    base = {
        "silicon_vendors": {},
        "platform_vendors": {},
        "processors": {},
        "system_modules": {},
        "platforms": {},
    }
    base.update(sections)
    return base


def test_entity_id_mismatch_detected():
    data = make_data(
        silicon_vendors={"ti": {"id": "texas", "type": "silicon_vendor"}}
    )
    errors = hw_reg_checker.validate_entity_ids(data)
    assert len(errors) == 1
    assert "does not match its key" in errors[0]


def test_entity_id_match_passes():
    data = make_data(
        silicon_vendors={"ti": {"id": "ti", "type": "silicon_vendor"}}
    )
    assert hw_reg_checker.validate_entity_ids(data) == []


def test_dangling_processor_vendor_ref():
    data = make_data(processors={"am625": {"id": "am625", "vendor_id": "ti"}})
    errors = hw_reg_checker.validate_references(data)
    assert len(errors) == 1
    assert "vendor_id" in errors[0]


def test_valid_references_pass():
    data = make_data(
        silicon_vendors={"ti": {"id": "ti"}},
        platform_vendors={"ti": {"id": "ti"}},
        processors={"am625": {"id": "am625", "vendor_id": "ti"}},
        platforms={
            "am62-sk": {
                "id": "am62-sk",
                "vendor_id": "ti",
                "processor_id": "am625",
            }
        },
    )
    assert hw_reg_checker.validate_references(data) == []


def test_duplicate_id_across_files_detected():
    file_a = make_data(processors={"am625": {"id": "am625", "vendor_id": "ti"}})
    file_b = make_data(processors={"am625": {"id": "am625", "vendor_id": "ti"}})
    merged, errors = hw_reg_checker.merge_registries(
        [("ti.yaml", file_a), ("other.yaml", file_b)]
    )
    assert len(errors) == 1
    assert "ti.yaml" in errors[0] and "other.yaml" in errors[0]


def test_cross_file_reference_resolves():
    file_a = make_data(
        silicon_vendors={"ti": {"id": "ti"}},
        processors={"am625": {"id": "am625", "vendor_id": "ti"}},
    )
    file_b = make_data(
        platform_vendors={"toradex": {"id": "toradex"}},
        system_modules={
            "verdin-am62": {
                "id": "verdin-am62",
                "type": "system_on_module",
                "vendor_id": "toradex",
                "processor_id": "am625",
            }
        },
    )
    merged, errors = hw_reg_checker.merge_registries(
        [("ti.yaml", file_a), ("toradex.yaml", file_b)]
    )
    assert errors == []
    assert hw_reg_checker.validate_references(merged) == []


def test_merged_dangling_reference_detected():
    file_a = make_data(
        system_modules={
            "som-x": {
                "id": "som-x",
                "vendor_id": "nobody",
                "processor_id": "ghost",
            }
        }
    )
    merged, errors = hw_reg_checker.merge_registries([("a.yaml", file_a)])
    assert errors == []
    ref_errors = hw_reg_checker.validate_references(merged)
    assert len(ref_errors) == 2
