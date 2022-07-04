from typing import List, Dict, Union

from dash import callback, Input, Output, html

from dash.development.base_component import Component
import pandas as pd
from webviz_config.webviz_plugin_subclasses import ViewABC
from webviz_config import WebvizSettings
import webviz_core_components as wcc

from .._plugin_ids import PluginIds
from ..view_elements import Graph
from ._view_funcions import (
    filter_data_frame,
    create_graph,
)
from ..shared_settings._filter import Filter


class PvtView(ViewABC):
    class Ids:
        # pylint disable too few arguments
        PVT_GRAPHS = "formation-volume-factor"
        VISCOSITY = "viscosity"
        DENSITY = "density"
        GAS_OIL_RATIO = "gas-oil-ratio"

    PHASES = ["OIL", "GAS", "WATER"]

    def __init__(self, pvt_df: pd.DataFrame, webviz_settings: WebvizSettings) -> None:
        super().__init__("Pvt View")

        self.phases_additional_info = Filter.phases_additional_info

        self.pvt_df = pvt_df
        self.plotly_theme = webviz_settings.theme.plotly_theme

        self.phases_additional_info: List[str] = []
        if self.pvt_df["KEYWORD"].str.contains("PVTO").any():
            self.phases_additional_info.append("PVTO")
        elif self.pvt_df["KEYWORD"].str.contains("PVDO").any():
            self.phases_additional_info.append("PVDO")
        elif self.pvt_df["KEYWORD"].str.contains("PVCDO").any():
            self.phases_additional_info.append("PVCDO")
        if self.pvt_df["KEYWORD"].str.contains("PVTG").any():
            self.phases_additional_info.append("PVTG")
        elif self.pvt_df["KEYWORD"].str.contains("PVDG").any():
            self.phases_additional_info.append("PVDG")
        if self.pvt_df["KEYWORD"].str.contains("PVTW").any():
            self.phases_additional_info.append("PVTW")

        column = self.add_column(PvtView.Ids.PVT_GRAPHS)

        #column.add_view_element(Graph(), PvtView.Ids.PVT_GRAPHS)

    @staticmethod
    def plot_visibility_options(phase: str = "") -> Dict[str, str]:
        options = {
            "fvf": "Formation Volume Factor",
            "viscosity": "Viscosity",
            "density": "Density",
        }
        if phase == "PVTO":
            options["ratio"] = "Gas/Oil Ratio (Rs)"
        if phase == "PVTG":
            options["ratio"] = "Vaporized Oil Ratio (Rv)"
        return options

    @property
    def phases(self) -> Dict[str, str]:
        phase_descriptions: Dict[str, str] = {}
        for i, phase in enumerate(PvtView.PHASES):
            phase_descriptions[phase] = self.phases_additional_info[i]
        return phase_descriptions

    @property
    def ensembles(self) -> List[str]:
        return list(self.pvt_df["ENSEMBLE"].unique())

    @property
    def pvtnums(self) -> List[str]:
        return list(self.pvt_df["PVTNUM"].unique())

    @property
    def ensemble_colors(self) -> Dict[str, List[str]]:
        return {
            ensemble: self.plotly_theme["layout"]["colorway"][
                self.ensembles.index(ensemble)
            ]
            for ensemble in self.ensembles
        }

    @property
    def pvtnum_colors(self) -> Dict[str, List[str]]:
        return {
            pvtnum: self.plotly_theme["layout"]["colorway"][self.pvtnums.index(pvtnum)]
            for pvtnum in self.pvtnums
        }

    def set_callbacks(self) -> None:
        @callback(
            Output(
                self.layout_element(PvtView.Ids.PVT_GRAPHS)
                .get_unique_id()
                .to_string(),
                "children",
            ),
            Input(self.get_store_unique_id(PluginIds.Stores.SELECTED_COLOR), "data"),
            Input(
                self.get_store_unique_id(PluginIds.Stores.SELECTED_ENSEMBLES), "data"
            ),
            Input(self.get_store_unique_id(PluginIds.Stores.SELECTED_PHASE), "data"),
            Input(self.get_store_unique_id(PluginIds.Stores.SELECTED_PVTNUM), "data"),
            Input(
                self.get_store_unique_id(PluginIds.Stores.SELECTED_SHOW_PLOTS), "data"
            ),
        )
        def _update_plots(
            color_by: str,
            ensembles: List[str],
            phase: str,
            pvtnum: List[str],
            plots_visibility: Union[List[str], str],
        ) -> List[Component]:

            PVT_df = filter_data_frame(self.pvt_df, ensembles, pvtnum)

            if color_by == "ENSEMBLE":
                colors = self.ensemble_colors
            elif color_by == "PVTNUM":
                colors = self.pvtnum_colors

            plots_list = []

            for plot in plots_visibility:
                plots_list.append(
                    wcc.WebvizViewElement(
                            id=self.unique_id(plot),
                            children = create_graph(
                                PVT_df,
                                color_by,
                                colors,
                                phase,
                                plot,
                                self.plot_visibility_options(self.phases[phase])[plot],
                                self.plotly_theme,
                            ), ) 
                )


            return plots_list
