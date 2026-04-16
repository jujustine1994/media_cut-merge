import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_main_importable():
    import main
    assert callable(getattr(main, 'ToolApp', None)), "ToolApp class not found"


def test_helpers_still_present():
    import main
    for name in ['validate_time', 'time_to_seconds', 'build_split_cmd',
                 'build_merge_list', 'build_convert_cmd', 'show_cth_banner']:
        assert callable(getattr(main, name, None)), f"{name} not found"
