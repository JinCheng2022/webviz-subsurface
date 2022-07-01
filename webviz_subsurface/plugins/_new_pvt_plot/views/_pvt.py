from typing import List

from dash import callback, Input, Output
import pandas as pd
from webviz_config.webviz_plugin_subclasses import ViewABC

from .._plugin_ids import PluginIds
from ..view_elements import Graph


class PvtView(ViewABC):
    class Ids:
        # pylint disable too few arguments
        FORMATION_VOLUME_FACTOR = "formation-volume-factor"
        VISCOSITY = "viscosity"
        DENSITY = "density"
        GAS_OIL_RATIO = "gas-oil-ratio"

    def __init__(self, pvt_df: pd.DataFrame) -> None:
        super().__init__("Pvt View")

        self.pvt_df = pvt_df

        column = self.add_column()

        first_row = column.make_row()
        first_row.add_view_element(Graph(), PvtView.Ids.FORMATION_VOLUME_FACTOR)
        first_row.add_view_element(Graph(), PvtView.Ids.VISCOSITY)

        second_row = column.make_row()
        second_row.add_view_element(Graph(), PvtView.Ids.DENSITY)
        second_row.add_view_element(Graph(), PvtView.Ids.GAS_OIL_RATIO)

    def set_callbacks(self) -> None:
        @callback(
            Output(self.view_element(PvtView.Ids.FORMATION_VOLUME_FACTOR)),
            Input(self.get_store_unique_id(PluginIds.Stores.SELECTED_COLOR), "data"),
            Input(self.get_store_unique_id(PluginIds.Stores.SELECTED_ENSEMBLES), "data"),
            Input(self.get_store_unique_id(PluginIds.Stores.SELECTED_PHASE), "data"),
            Input(self.get_store_unique_id(PluginIds.Stores.SELECTED_PVTNUM), "data"),
        )
        def _update_plots(
            color_by: str,
            ensembles: List[str],
            phase: str,
            pvtnum: List[str]
        ) -> dict:
            formation_volume_factor = {}
            return formation_volume_factor