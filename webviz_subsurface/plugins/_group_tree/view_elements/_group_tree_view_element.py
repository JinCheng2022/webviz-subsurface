from dash import html
from webviz_config.webviz_plugin_subclasses import ViewElementABC


class GroupTreeViewElement(ViewElementABC):
    class Ids:
        # pylint: disable=too-few-public-methods
        COMPONENT = "component"

    def __init__(self) -> None:
        super().__init__()

    def inner_layout(self) -> html.Div:
        return html.Div(
            id=self.register_component_unique_id(GroupTreeViewElement.Ids.COMPONENT)
        )
