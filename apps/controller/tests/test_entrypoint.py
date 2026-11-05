from importlib.metadata import entry_points


def test_console_script_resolves_to_main_run() -> None:
    (script,) = [ep for ep in entry_points(group="console_scripts") if ep.name == "purr-controller"]
    assert script.value == "purr_controller.main:run"
    assert callable(script.load())
