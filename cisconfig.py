from textual.app import App, ComposeResult
from textual.widgets import (
    Select,
    Input,
    TextArea,
    Button,
    Header,
)
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.reactive import reactive
import pyperclip
from textual.theme import Theme

# /* Template System */

class CiscoTemplate:
    def __init__(self, name: str, metadata: str, config: str, variables: list[str]):
        self.name = name
        self.metadata = metadata
        self.config = config
        self.variables = variables

# Add new templates to this list here.

TEMPLATES = [
    CiscoTemplate(
        name="Basic Interface",
        metadata="This metadata field does nothing in the code; use it for notes.",
        config="""
interface {interface}
ip address {ip} {subnet}
no shutdown
""",
        variables=["interface", "ip", "subnet"]
    ),
    CiscoTemplate(
        name="Basic Configuration",
        metadata="",
        config="""
no ip domain-lookup
banner motd "{motd}"
security password min-length {password_min_length}
login block-for {login_block_for} attempts {login_attempts} within {login_time_within}
line console 0
exec-timeout {exec_timeout_mins} {exec_timeout_secs}
password {console_password}
login
exit
enable secret {enable_password}
service password-encryption
exit
copy running-config startup-config
""",
        variables=["motd", "password_min_length", "login_block_for", "login_attempts",
                   "login_time_within", "exec_timeout_mins", "exec_timeout_secs",
                   "console_password", "enable_password"]
    ),
    CiscoTemplate(
        name="Router-on-a-Stick (3)",
        metadata="Router-on-a-stick for three subinterfaces.",
        config="""
interface {interface_type} {interface_number}/0.10
encapsulation dot1Q {VLAN_number_0}
ip address {VLAN_IP_and_subnet_0}
exit
interface {interface_type} {interface_number}/0.20
encapsulation dot1Q {VLAN_number_1}
ip address {VLAN_IP_and_subnet_1}
exit
interface {interface_type} {interface_number}/0.30
encapsulation dot1Q {VLAN_number_2}
ip address {VLAN_IP_and_subnet_2}
exit
interface {interface_type} {interface_number}/0
no shutdown
""",
        variables=["interface_type", "interface_number", "VLAN_number_0", "VLAN_IP_and_subnet_0", 
                   "VLAN_number_1", "VLAN_IP_and_subnet_1", "VLAN_number_2", "VLAN_IP_and_subnet_2"]
    ),
]

# /* Colour theme */

console_theme = Theme(
name="console",
# Base colors (11 are supported; we provide the important ones explicitly)
primary="#FFFFFF",
secondary="#FFFFFF",
accent="#FFFFFF",
foreground="#FFFFFF",
background="#000000",
surface="#000000",
panel="#000000",
success="#FFFFFF",
warning="#FFFFFF",
error="#FFFFFF",
# Declare this as a dark theme so Textual generates appropriate shades.
dark=True,
# Additional small variables to tweak cursors, inputs, footers to match a plain console.
variables={
# Keep block cursor simple (no text-style like inverse or bold)
"block-cursor-text-style": "none",
# Make footer key hints plain white
"footer-key-foreground": "#FFFFFF",
# Selection as a subtle white overlay (30% opacity)
"input-selection-background": "#FFFFFF 30%",
# Cursor color
"cursor": "#FFFFFF",
# Muted / disabled text (slightly dim white)
"foreground-muted": "#CCCCCC",
},
)

# /* Main Application */

class CiscoTemplateApp(App):
    CSS = """
    Screen {
        padding: 1;
    }

    #inputs {
        padding: 1;
        border: solid gray;
    }

    TextArea {
        height: 12;
    }

    #inputs_scroll {
        height: 18;
        border: solid gray;
        padding: 1;
    }

    #left_col, #right_col {
        width: 1fr;
    }
    """

    selected_template: reactive[CiscoTemplate | None] = reactive(None)
    values: reactive[dict] = reactive({})

    def on_mount(self) -> None:
        self.title = "cisconfig"
        # Register the theme
        self.register_theme(console_theme)
        self.theme = "console"

    def compose(self) -> ComposeResult:
        yield Header()

        yield Select(
            [(t.name, i) for i, t in enumerate(TEMPLATES)],
            prompt="Select a template...",
            id="template_select",
        )

        yield VerticalScroll(
            Horizontal(
                Vertical(id="left_col"),
                Vertical(id="right_col"),
            ),
            id="inputs_scroll",
        )

        yield TextArea(id="output")

        yield Button("Copy to Clipboard", id="copy")

    # /* Event Handlers */

    def on_select_changed(self, event: Select.Changed) -> None:
        left_col = self.query_one("#left_col", Vertical)
        right_col = self.query_one("#right_col", Vertical)
        output = self.query_one("#output", TextArea)

        if event.value is Select.BLANK:
            self.selected_template = None
            self.values = {}
            left_col.remove_children()
            right_col.remove_children()
            output.text = ""
            return

        template = TEMPLATES[event.value]
        self.selected_template = template
        self.values = {var: "" for var in template.variables}

        left_col.remove_children()
        right_col.remove_children()

        midpoint = (len(template.variables) + 1) // 2

        for i, var in enumerate(template.variables):
            target = left_col if i < midpoint else right_col
            target.mount(Input(placeholder=var, id=f"input_{var}"))

        self.update_output()


    def on_input_changed(self, event: Input.Changed) -> None:
        if not self.selected_template:
            return

        var_name = event.input.placeholder
        self.values[var_name] = event.value
        self.update_output()

    def update_output(self) -> None:
        if not self.selected_template:
            return

        try:
            rendered = self.selected_template.config.format(**self.values)
        except KeyError:
            rendered = ""

        self.query_one("#output", TextArea).text = rendered.strip()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "copy":
            output = self.query_one("#output", TextArea).text
            pyperclip.copy(output)
            self.notify("Copied to clipboard.")


if __name__ == "__main__":
    CiscoTemplateApp().run()
