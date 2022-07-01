from typing import Union, Dict,List

import pandas as pd


def create_hovertext(
    phase: str,
    keyword: str,
    constant_group: str,
    group: str,
    color_by: str,
    realization: str,
    ratio_value: float,
) -> str:
    hovertext: Union[str, list] = ""
    if phase == "OIL":
        # pylint: disable=consider-using-f-string
        hovertext = "{} Pvtnum: {}<br />Realization: {}, Ensemble: {}".format(
            f"Rs = {ratio_value}" if keyword == "PVTO" else "",
            group if color_by == "PVTNUM" else constant_group,
            realization,
            group if color_by == "ENSEMBLE" else constant_group,
        )
    elif phase == "GAS":
        # pylint: disable=consider-using-f-string
        hovertext = (
            "{}"
            "Pvtnum: "
            "{}<br />"
            "Realization: {}, Ensemble: "
            "{}".format(
                f"Rv = {ratio_value}, " if keyword == "PVTG" else "",
                group if color_by == "PVTNUM" else constant_group,
                realization,
                group if color_by == "ENSEMBLE" else constant_group,
            )
        )
    else:
        hovertext = (
            f"Pvtnum: {group if color_by == 'PVTNUM' else constant_group}<br />"
            f"Realization: {realization}, "
            f"Ensemble: {group if color_by == 'ENSEMBLE' else constant_group}"
        )

    return hovertext

def create_traces(
    data_frame: pd.DataFrame,
    color_by: str,
    colors: Dict[str, List[str]],
    phase: str,
    column_name: str,
    show_scatter_values: bool,
    show_border_values: bool,
    show_border_markers: bool = False,
) -> List[dict]:
    """Renders line traces for individual realizations"""
    # pylint: disable-msg=too-many-locals
    # pylint: disable=too-many-nested-blocks
    # pylint: disable=too-many-branches

    traces = []
    hovertext: Union[List[str], str]
    border_value_pressure: Dict[str, list] = {}
    border_value_dependent: Dict[str, list] = {}

    dim_column_name = "RATIO"

    if phase == "OIL":
        data_frame = data_frame.loc[
            (data_frame["KEYWORD"] == "PVTO") | (data_frame["KEYWORD"] == "PVDO")
        ]
    elif phase == "GAS":
        data_frame = data_frame.loc[
            (data_frame["KEYWORD"] == "PVTG") | (data_frame["KEYWORD"] == "PVDG")
        ]
        dim_column_name = "PRESSURE"
    else:
        data_frame = data_frame.loc[data_frame["KEYWORD"] == "PVTW"]
        dim_column_name = "PRESSURE"

    data_frame = data_frame.sort_values(
        ["PRESSURE", "VOLUMEFACTOR", "VISCOSITY"],
        ascending=[True, True, True],
    )

    constant_group = (
        data_frame["PVTNUM"].iloc[0]
        if color_by == "ENSEMBLE"
        else data_frame["ENSEMBLE"].iloc[0]
    )

    for (group, grouped_data_frame) in data_frame.groupby(color_by):
        for set_no, set_value in enumerate(
            grouped_data_frame[dim_column_name].unique()
        ):
            for realization_no, (realization, realization_data_frame) in enumerate(
                grouped_data_frame.groupby("REAL")
            ):
                if group not in border_value_pressure:
                    border_value_pressure[group] = []
                    border_value_dependent[group] = []
                try:
                    border_value_pressure[group].append(
                        realization_data_frame.loc[
                            realization_data_frame[dim_column_name] == set_value
                        ]["PRESSURE"].iloc[0]
                    )
                    if column_name == "VISCOSITY":
                        if phase == "OIL":
                            border_value_dependent[group].append(
                                realization_data_frame[
                                    (
                                        realization_data_frame[dim_column_name]
                                        == set_value
                                    )
                                ]["VISCOSITY"].iloc[0]
                            )
                        else:
                            border_value_dependent[group].append(
                                realization_data_frame[
                                    (
                                        realization_data_frame[dim_column_name]
                                        == set_value
                                    )
                                ]["VISCOSITY"].max()
                            )
                    else:
                        border_value_dependent[group].append(
                            realization_data_frame.loc[
                                realization_data_frame[dim_column_name] == set_value
                            ][column_name].iloc[0]
                        )
                except IndexError as exc:
                    raise IndexError(
                        "This error is most likely due to PVT differences between "
                        "realizations within the same ensemble. This is currently not "
                        "supported."
                    ) from exc

                if show_scatter_values:
                    if phase == "GAS":
                        hovertext = [
                            create_hovertext(
                                phase,
                                realization_data_frame["KEYWORD"].iloc[0],
                                constant_group,
                                group,
                                color_by,
                                realization,
                                realization_data_frame.loc[
                                    (realization_data_frame["PRESSURE"] == y)
                                    & (realization_data_frame[column_name] == x)
                                ]["RATIO"].iloc[0],
                            )
                            for x, y in zip(
                                realization_data_frame.loc[
                                    realization_data_frame["PRESSURE"] == set_value
                                ][column_name],
                                realization_data_frame.loc[
                                    realization_data_frame["PRESSURE"] == set_value
                                ].PRESSURE,
                            )
                        ]
                    else:
                        hovertext = create_hovertext(
                            phase,
                            realization_data_frame["KEYWORD"].iloc[0],
                            constant_group,
                            group,
                            color_by,
                            realization,
                            set_value,
                        )

                    traces.extend(
                        [
                            {
                                "type": "scatter",
                                "x": realization_data_frame.loc[
                                    realization_data_frame[dim_column_name] == set_value
                                ]["PRESSURE"],
                                "y": realization_data_frame.loc[
                                    realization_data_frame[dim_column_name] == set_value
                                ][column_name],
                                "xaxis": "x",
                                "yaxis": "y",
                                "hovertext": hovertext,
                                "name": group,
                                "legendgroup": group,
                                "marker": {
                                    "color": colors.get(
                                        group, colors[list(colors.keys())[-1]]
                                    )
                                },
                                "showlegend": realization_no == 0 and set_no == 0,
                            }
                        ]
                    )
    if show_border_values:
        for group, group_border_value_pressure in border_value_pressure.items():
            traces.extend(
                [
                    {
                        "type": "scatter",
                        "mode": ("lines+markers" if show_border_markers else "lines"),
                        "x": group_border_value_pressure,
                        "y": border_value_dependent[group],
                        "xaxis": "x",
                        "yaxis": "y",
                        "legendgroup": group,
                        "line": {
                            "width": 1,
                            "color": colors.get(group, colors[list(colors.keys())[-1]]),
                        },
                        "showlegend": not show_scatter_values,
                    }
                ]
            )
    return traces