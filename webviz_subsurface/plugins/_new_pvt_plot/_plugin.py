from typing import Type, List, Tuple, Callable, Dict, Any

from dash.development.base_component import Component
from webviz_config import WebvizPluginABC, WebvizSettings
from dash import Dash

from ._error import error
from .views import PvtView
from ._plugin_ids import PluginIds
from .shared_settings import Filter, ShowPlots
from ..._datainput.pvt_data import load_pvt_csv, load_pvt_dataframe


class PvtPlotter(WebvizPluginABC):

    PHASES = ["OIL", "GAS", "WATER"]

    def __init__(
        self,
        app: Dash,
        webviz_settings: WebvizSettings,
        ensembles: List[str],
        pvt_relative_file_path: str = None,
        read_from_init_file: bool = False,
        drop_ensemble_duplicates: bool = False,
    ) -> None:
        super().__init__(stretch=True)

        self.ensemble_paths = {
            ensemble: webviz_settings.shared_settings["scratch_ensembles"][ensemble]
            for ensemble in ensembles
        }

        self.plotly_theme = webviz_settings.theme.plotly_theme

        self.pvt_relative_file_path = pvt_relative_file_path

        self.read_from_init_file = read_from_init_file

        self.drop_ensemble_duplicates = drop_ensemble_duplicates

        if self.pvt_relative_file_path is None:
            self.pvt_df = load_pvt_dataframe(
                self.ensemble_paths,
                use_init_file=read_from_init_file,
                drop_ensemble_duplicates=drop_ensemble_duplicates,
            )
        else:
            # Load data from all ensembles into a pandas DataFrame
            self.pvt_df = load_pvt_csv(
                ensemble_paths=self.ensemble_paths,
                csv_file=self.pvt_relative_file_path,
                drop_ensemble_duplicates=drop_ensemble_duplicates,
            )

            self.pvt_df = self.pvt_df.rename(str.upper, axis="columns").rename(
                columns={"TYPE": "KEYWORD", "RS": "RATIO", "R": "RATIO", "GOR": "RATIO"}
            )

        # Ensure that the identifier string "KEYWORD" is contained in the header columns
        if "KEYWORD" not in self.pvt_df.columns:
            raise ValueError(
                (
                    "There has to be a KEYWORD or TYPE column with corresponding Eclipse keyword."
                    "When not providing a csv file, make sure ecl2df is installed."
                )
            )

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

        # Error messages
        self.error_message = ""

        self.add_store(
            PluginIds.Stores.SELECTED_COLOR, WebvizPluginABC.StorageType.SESSION
        )
        self.add_store(
            PluginIds.Stores.SELECTED_ENSEMBLES, WebvizPluginABC.StorageType.SESSION
        )

        self.add_store(
            PluginIds.Stores.SELECTED_PHASE, WebvizPluginABC.StorageType.SESSION
        )
        self.add_store(
            PluginIds.Stores.SELECTED_PVTNUM, WebvizPluginABC.StorageType.SESSION
        )

        self.add_store(
            PluginIds.Stores.SELECTED_SHOW_PLOTS, WebvizPluginABC.StorageType.SESSION
        )

        self.add_shared_settings_group(
            Filter(self.pvt_df), PluginIds.SharedSettings.FILTER
        )

        self.add_shared_settings_group(
            ShowPlots(self.pvt_df), PluginIds.SharedSettings.SHOWPLOTS
        )

        self.add_view(
            PvtView(self.pvt_df, webviz_settings),
            PluginIds.PvtID.INDICATORS,
            PluginIds.PvtID.GROUP_NAME,
        )

    def add_webvizstore(
        self,
    ) -> List[Tuple[Callable, List[Dict[str, Any]]]]:
        return (
            [
                (
                    load_pvt_dataframe,
                    [
                        {
                            "ensemble_paths": self.ensemble_paths,
                            "use_init_file": self.read_from_init_file,
                            "drop_ensemble_duplicates": self.drop_ensemble_duplicates,
                        }
                    ],
                )
            ]
            if self.pvt_relative_file_path is None
            else [
                (
                    load_pvt_csv,
                    [
                        {
                            "ensemble_paths": self.ensemble_paths,
                            "csv_file": self.pvt_relative_file_path,
                            "drop_ensemble_duplicates": self.drop_ensemble_duplicates,
                        }
                    ],
                )
            ]
        )

    @property
    def layout(self) -> Type[Component]:
        return error(self.error_message)
