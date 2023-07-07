from pyecharts import options as opts
from pyecharts.charts import Bar, Grid, Kline, Line, Scatter
from pyecharts.commons.utils import JsCode

width_set = "1400px"
def plot_kline_volume_signal_adept(data, lines, bars_name = "volume", grid_lines = None, long_short = None, path = '.'):
    kline = (
            Kline(init_opts=opts.InitOpts(width=width_set,height="1000px")) # 设置画布大小
            .add_xaxis(xaxis_data=list(data.index)) # 将原始数据的index转化为list作为横坐标
            .add_yaxis(series_name="klines",
            y_axis=data[["open","close","low","high"]].values.tolist(), 
            # 纵坐标采用OPEN、CLOSE、LOW、HIGH，注意顺序
            itemstyle_opts=opts.ItemStyleOpts(color="#ec0000", color0="#00da3c"),
            yaxis_index=0)
            .extend_axis(yaxis=opts.AxisOpts( type_="value", position="right", name='抄底，健康度，vr'))
            
            .set_global_opts(legend_opts=opts.LegendOpts(is_show=True, pos_bottom=10, pos_left="center"),
                datazoom_opts=[
                    opts.DataZoomOpts(
                        is_show=False,
                        type_="inside",
                        xaxis_index=[0,1],
                        range_start=95,
                        range_end=100,
                    ),
                    opts.DataZoomOpts(
                        is_show=True,
                        xaxis_index=[0,1],
                        type_="slider",
                        pos_top="85%",
                        range_start=95,
                        range_end=100,
                    ),
                ],
                yaxis_opts=opts.AxisOpts(
                    is_scale=True,
                    splitarea_opts=opts.SplitAreaOpts(
                        is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1),
                    ),
                    name='价格'
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="cross",
                    background_color="rgba(245, 245, 245, 0.8)",
                    border_width=1,
                    border_color="#ccc",
                    textstyle_opts=opts.TextStyleOpts(color="#000"),
                ),
                # visualmap_opts=opts.VisualMapOpts(
                #     is_show=False,
                #     dimension=2,
                #     series_index=5,
                #     is_piecewise=True,
                #     pieces=[
                #         {"value": 1, "color": "#00da3c"},
                #         {"value": -1, "color": "#ec0000"},
                #     ],
                # ),
                axispointer_opts=opts.AxisPointerOpts(
                    is_show=True,
                    link=[{"xAxisIndex": "all"}],
                    label=opts.LabelOpts(background_color="#777"),
                ),
                brush_opts=opts.BrushOpts(
                    x_axis_index="all",
                    brush_link="all",
                    out_of_brush={"colorAlpha": 0.1},
                    brush_type="lineX",
                ),
            )
        )

    
    line=(Line()
            .add_xaxis(xaxis_data=list(data.index))
            .add_yaxis(
                series_name="risk",
                y_axis=data[lines[0]].tolist(),
                # xaxis_index=1,
                yaxis_index=1,
                label_opts=opts.LabelOpts(is_show=False))
            
            
                )
        
    if len(lines) > 1:
        for i in lines[1:]:
            line=line.add_yaxis(
                    series_name=i,
                    y_axis=data[i].tolist(),
                    # xaxis_index=1,
                    yaxis_index=1,
                    label_opts=opts.LabelOpts(is_show=False),
            )
    
    if long_short is not None:
        # assert isinstance(long_short, list)
        scatter = data.dropna()
        scatter = scatter.loc[scatter.volumne != 1]
        scatterlong = scatter.loc[scatter.direction == 'LONG']
        scattershort = scatter.loc[scatter.direction == 'SHORT']
        line11 = (
                Scatter()
                .add_xaxis(xaxis_data= list(scatterlong.index))
                .add_yaxis(series_name='买',
                        yaxis_index=0,
                        y_axis=[list(z) for z in zip(scatterlong['low'].values * 0.98, scatterlong['direction'].values)] ,
                        # xaxis_index=0,
                        symbol_size=25,#设置散点的大小
                        symbol='image://https://tse4-mm.cn.bing.net/th/id/OIP-C.jR5J6jZoUh3-V9-asM7pDQHaHr?pid=ImgDet&rs=1',
                        # label_opts=opts.LabelOpts(formatter=JsCode(
                        #         # 构造回调函数
                        #         "function(params){return params.value[1] +' : '+ params.value[2];}"
                        #     ),
                        #     # font_size=35  #params.value[1]对应y轴Faker.values() :  params.value[2]对应y轴Faker.choose())
                        # )
                        )                

                # .set_series_opts(label_opts = opts.LabelOpts(is_show =True))
                # .set_global_opts(legend_opts=opts.LegendOpts(is_show=False))
                # .set_global_opts(visualmap_opts=opts.VisualMapOpts(is_show=False))
                )
        line2l = (
                Scatter()
                .add_xaxis(xaxis_data= list(scattershort.index))
                                .add_yaxis(series_name='卖',
                        yaxis_index=0,
                        y_axis=[list(z) for z in zip(scattershort['high'].values * 1.02, scattershort['direction'].values)] ,
                        # xaxis_index=0,
                        symbol_size=25,#设置散点的大小
                        symbol='image://https://img.tukuppt.com/ad_preview/00/20/72/Ff8uA6zAwB.jpg!/fw/260',
                        color='Green',
                        # label_opts=opts.LabelOpts(formatter=JsCode(
                        #         # 构造回调函数
                        #         "function(params){return params.value[1] +' : '+ params.value[2];}",
                                
                        #     )  #params.value[1]对应y轴Faker.values() :  params.value[2]对应y轴Faker.choose())
                        #     ,
                        #     # font_size=35
                        # )
                        )          
        )
        kline = kline.overlap(line11)
        kline = kline.overlap(line2l)

    bar = (
            Bar()
            .add_xaxis(xaxis_data=list(data.index))
            .add_yaxis(
                series_name="volume",
                y_axis=data[bars_name].tolist(),
                xaxis_index=1,
                yaxis_index=2,
                label_opts=opts.LabelOpts(is_show=False),
                itemstyle_opts=opts.ItemStyleOpts(
                    color=JsCode(
                        """
                    function(params) {
                        var colorList;
                        if (barData[params.dataIndex][1] > barData[params.dataIndex][0]) {
                            colorList = '#ef232a';
                        } else {
                            colorList = '#14b143';
                        }
                        return colorList;
                    }
                    """
                    )
                ),
            )
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    grid_index=2,
                    axislabel_opts=opts.LabelOpts(is_show=False),
                ),                
                yaxis_opts=opts.AxisOpts(
                    is_scale=True,
                    splitarea_opts=opts.SplitAreaOpts(
                        is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1),
                    ),
                    name='交易量'
                ),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )
    grid_chart = Grid(
        init_opts=opts.InitOpts(
            width=width_set,
            height="1000px",
            animation_opts=opts.AnimationOpts(animation=False),
        )
    )

    grid_chart.add_js_funcs("var barData={}".format(data[["open","close"]].values.tolist()))
    overlap_kline_line = kline.overlap(line)
    # overlap_kline_line = overlap_kline_line.overlap(block)
    # overlap_kline_line = line.overlap(kline)

    grid_chart.add(
        overlap_kline_line,
        #kline,
        grid_opts=opts.GridOpts(pos_left="11%", pos_right="8%", height="40%"),
        is_control_axis_index=True
    )

    grid_chart.add(
        bar,
        grid_opts=opts.GridOpts( pos_top="60%", height="30%"
        ),
        is_control_axis_index=True
    )

    if grid_lines is not None:
        
        new=(Line()
                .add_xaxis(xaxis_data=list(data.index))
                .add_yaxis(
                    series_name=grid_lines[0],
                    y_axis=data[grid_lines[0]].tolist(),
                    xaxis_index=2,
                    yaxis_index=3,
                    # label_opts=opts.LabelOpts(is_show=False)
                    )
                .set_global_opts(
                    xaxis_opts=opts.AxisOpts(
                    type_="category",
                    grid_index=2,
                    axislabel_opts=opts.LabelOpts(is_show=False)),                
                    yaxis_opts=opts.AxisOpts(
                            is_scale=True,
                            splitarea_opts=opts.SplitAreaOpts(
                            is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1))
                            ,name='价格'),
                        legend_opts=opts.LegendOpts(is_show=False),
                )
            )

        grid_chart.add(
            new,
            grid_opts=opts.GridOpts(
                pos_left="10%", pos_right="8%", pos_top="60%", height="20%"
            ),
            is_control_axis_index=True
        )

    grid_chart.render(f"{path}/kline_volume_signal.html")
    return grid_chart

if __name__ == '__main__':
    import copy
    import datetime

    import pandas as pd
    from pandas import DataFrame

    from utils.basic import name_2_symbol, rename_dataframe
    from stock_strategy import StockIndex, barloader, stock_etf_hist_dataloader
    print('rerun')
    stockindex = StockIndex()
    hist = stock_etf_hist_dataloader('sh510300')
    hist = rename_dataframe(hist)
    hist['date'] = pd.to_datetime(hist['date']).dt.date
    stockindex.set_am(hist)
    setattr(stockindex, 'origin_data', hist.set_index('date')) 
    stockindex.origin_data['risk'] = list(stockindex.risk()[1].squeeze())
    plot_kline_volume_signal_adept(stockindex.origin_data, ['risk'] )

    