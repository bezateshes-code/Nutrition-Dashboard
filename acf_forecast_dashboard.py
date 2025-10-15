import streamlit as st
import pandas as pd
import io
import altair as alt
from datetime import date
import math

# ------------------------------------------------------------
# Action Against Hunger theme
AAH_BLUE = "#0072CE"
AAH_GREEN = "#78BE20"
AAH_ORANGE = "#F58220"
AAH_GREY = "#4D4D4D"

st.set_page_config(page_title="Action Against Hunger – Ethiopia Forecast Dashboard", layout="wide")

# ------------------------------------------------------------
# Header (replace with your local logo if you have one)
st.markdown(
    f"""
    <div style="display:flex; align-items:center; background-color:{AAH_BLUE}; padding:12px;">
        <div style="width:10px; height:40px; background-color:{AAH_GREEN}; margin-right:12px;"></div>
        <h2 style="color:white; margin:0;">Action Against Hunger – Ethiopia Forecast Dashboard</h2>
    </div>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------------
# Embedded CSV (no external files needed)
CSV_DATA = """region,woreda,date,acute_cases,roll_mean,roll_std,variability_factor
amhara,beyeda,1/1/2019,0,,,
amhara,beyeda,2/1/2019,0,,,
amhara,beyeda,3/1/2019,0,0,0,
amhara,beyeda,4/1/2019,0,0,0,
amhara,beyeda,5/1/2019,0,0,0,
amhara,beyeda,6/1/2019,0,0,0,
amhara,beyeda,7/1/2019,0,0,0,
amhara,beyeda,8/1/2019,0,0,0,
amhara,beyeda,9/1/2019,0,0,0,
amhara,beyeda,10/1/2019,0,0,0,
amhara,beyeda,11/1/2019,0,0,0,
amhara,beyeda,12/1/2019,0,0,0,
amhara,beyeda,1/1/2020,0,0,0,
amhara,beyeda,2/1/2020,0,0,0,
amhara,beyeda,3/1/2020,0,0,0,
amhara,beyeda,4/1/2020,0,0,0,
amhara,beyeda,5/1/2020,0,0,0,
amhara,beyeda,6/1/2020,0,0,0,
amhara,beyeda,7/1/2020,0,0,0,
amhara,beyeda,8/1/2020,0,0,0,
amhara,beyeda,9/1/2020,0,0,0,
amhara,beyeda,10/1/2020,0,0,0,
amhara,beyeda,11/1/2020,0,0,0,
amhara,beyeda,12/1/2020,0,0,0,
amhara,beyeda,1/1/2021,0,0,0,
amhara,beyeda,2/1/2021,0,0,0,
amhara,beyeda,3/1/2021,0,0,0,
amhara,beyeda,4/1/2021,0,0,0,
amhara,beyeda,5/1/2021,0,0,0,
amhara,beyeda,6/1/2021,0,0,0,
amhara,beyeda,7/1/2021,0,0,0,
amhara,beyeda,8/1/2021,0,0,0,
amhara,beyeda,9/1/2021,0,0,0,
amhara,beyeda,10/1/2021,0,0,0,
amhara,beyeda,11/1/2021,0,0,0,
amhara,beyeda,12/1/2021,0,0,0,
amhara,beyeda,1/1/2022,0,0,0,
amhara,beyeda,2/1/2022,0,0,0,
amhara,beyeda,3/1/2022,0,0,0,
amhara,beyeda,4/1/2022,0,0,0,
amhara,beyeda,5/1/2022,0,0,0,
amhara,beyeda,6/1/2022,0,0,0,
amhara,beyeda,7/1/2022,467,77.83333333,190.6519516,2.449489743
amhara,beyeda,8/1/2022,341,134.6666667,212.395543,1.577194626
amhara,beyeda,9/1/2022,130,156.3333333,202.3014253,1.294038968
amhara,beyeda,10/1/2022,185,187.1666667,187.2468068,1.000428175
amhara,beyeda,11/1/2022,235,226.3333333,163.3152371,0.721569531
amhara,beyeda,12/1/2022,684,340.3333333,206.6955894,0.60733278
amhara,beyeda,1/1/2023,209,297.3333333,201.8540727,0.67888141
amhara,beyeda,2/1/2023,290,288.8333333,200.7181274,0.694927158
amhara,beyeda,3/1/2023,268,311.8333333,186.263702,0.597318125
amhara,beyeda,4/1/2023,56,290.3333333,209.7910071,0.722586706
amhara,beyeda,5/1/2023,152,276.5,216.789068,0.784047262
amhara,beyeda,6/1/2023,223,199.6666667,85.29165649,0.427170233
amhara,beyeda,7/1/2023,142,188.5,88.16291737,0.467707784
amhara,beyeda,8/1/2023,130,161.8333333,74.4537888,0.460064606
amhara,beyeda,9/1/2023,250,158.8333333,69.51954162,0.437688615
amhara,beyeda,10/1/2023,201,183,48.71139497,0.266182486
amhara,beyeda,11/1/2023,448,232.3333333,115.3475906,0.496474565
amhara,beyeda,12/1/2023,425,266,139.1100284,0.522970032
amhara,beyeda,1/1/2024,114,261.3333333,144.4682203,0.552812067
amhara,beyeda,2/1/2024,84,253.6666667,153.7539159,0.606125818
amhara,beyeda,3/1/2024,230,250.3333333,154.0657868,0.615442557
amhara,beyeda,4/1/2024,281,263.6666667,152.3951005,0.577983946
amhara,beyeda,5/1/2024,369,250.5,135.7921205,0.542084314
amhara,beyeda,6/1/2024,157,205.8333333,108.1839483,0.525590032
amhara,beyeda,7/1/2024,0,186.8333333,134.3777015,0.719238367
amhara,beyeda,8/1/2024,0,172.8333333,150.6272441,0.871517324
amhara,beyeda,9/1/2024,0,134.5,162.0058641,1.204504566
amhara,beyeda,10/1/2024,0,87.66666667,151.4578049,1.727655569
amhara,beyeda,11/1/2024,0,26.16666667,64.0949816,2.449489743
amhara,beyeda,12/1/2024,0,0,0,
amhara,debark_town,1/1/2019,0,,,
amhara,debark_town,2/1/2019,0,,,
amhara,debark_town,3/1/2019,0,0,0,
amhara,debark_town,4/1/2019,0,0,0,
amhara,debark_town,5/1/2019,0,0,0,
amhara,debark_town,6/1/2019,0,0,0,
amhara,debark_town,7/1/2019,0,0,0,
amhara,debark_town,8/1/2019,0,0,0,
amhara,debark_town,9/1/2019,0,0,0,
amhara,debark_town,10/1/2019,0,0,0,
amhara,debark_town,11/1/2019,0,0,0,
amhara,debark_town,12/1/2019,0,0,0,
amhara,debark_town,1/1/2020,0,0,0,
amhara,debark_town,2/1/2020,0,0,0,
amhara,debark_town,3/1/2020,0,0,0,
amhara,debark_town,4/1/2020,0,0,0,
amhara,debark_town,5/1/2020,0,0,0,
amhara,debark_town,6/1/2020,0,0,0,
amhara,debark_town,7/1/2020,0,0,0,
amhara,debark_town,8/1/2020,0,0,0,
amhara,debark_town,9/1/2020,0,0,0,
amhara,debark_town,10/1/2020,0,0,0,
amhara,debark_town,11/1/2020,0,0,0,
amhara,debark_town,12/1/2020,0,0,0,
amhara,debark_town,1/1/2021,0,0,0,
amhara,debark_town,2/1/2021,0,0,0,
amhara,debark_town,3/1/2021,0,0,0,
amhara,debark_town,4/1/2021,0,0,0,
amhara,debark_town,5/1/2021,0,0,0,
amhara,debark_town,6/1/2021,0,0,0,
amhara,debark_town,7/1/2021,0,0,0,
amhara,debark_town,8/1/2021,0,0,0,
amhara,debark_town,9/1/2021,0,0,0,
amhara,debark_town,10/1/2021,0,0,0,
amhara,debark_town,11/1/2021,0,0,0,
amhara,debark_town,12/1/2021,0,0,0,
amhara,debark_town,1/1/2022,0,0,0,
amhara,debark_town,2/1/2022,0,0,0,
amhara,debark_town,3/1/2022,0,0,0,
amhara,debark_town,4/1/2022,0,0,0,
amhara,debark_town,5/1/2022,0,0,0,
amhara,debark_town,6/1/2022,0,0,0,
amhara,debark_town,7/1/2022,180,30,73.48469228,2.449489743
amhara,debark_town,8/1/2022,76,42.66666667,73.8286304,1.730358525
amhara,debark_town,9/1/2022,766,170.3333333,300.2836437,1.762917673
amhara,debark_town,10/1/2022,22,174,297.9127389,1.712142178
amhara,debark_town,11/1/2022,215,209.8333333,285.4683287,1.360452718
amhara,debark_town,12/1/2022,93,225.3333333,274.0946309,1.216396291
amhara,debark_town,1/1/2023,41,202.1666667,284.3739908,1.406631447
amhara,debark_town,2/1/2023,18,192.5,290.4415604,1.508787327
amhara,debark_town,3/1/2023,21,68.33333333,77.18462714,1.129531129
amhara,debark_town,4/1/2023,16,67.33333333,77.94014798,1.15752695
amhara,debark_town,5/1/2023,48,39.5,29.3035834,0.741862871
amhara,debark_town,6/1/2023,64,34.66666667,19.44907881,0.56103112
amhara,debark_town,7/1/2023,20,31.16666667,19.96413451,0.640560466
amhara,debark_town,8/1/2023,15,30.66666667,20.39280919,0.664982908
amhara,debark_town,9/1/2023,25,31.33333333,20.07652028,0.640740009
amhara,debark_town,10/1/2023,98,45,31.94996088,0.709999131
amhara,debark_town,11/1/2023,14,39.33333333,34.24422092,0.870615786
amhara,debark_town,12/1/2023,203,62.5,75.9229873,1.214767797
amhara,debark_town,1/1/2024,22,62.83333333,75.70314833,1.204824642
amhara,debark_town,2/1/2024,15,62.83333333,75.70314833,1.204824642
amhara,debark_town,3/1/2024,18,61.66666667,76.45303569,1.239778957
amhara,debark_town,4/1/2024,17,48.16666667,75.90366702,1.575854679
amhara,debark_town,5/1/2024,12,47.83333333,76.08788778,1.590687549
amhara,debark_town,6/1/2024,69,25.5,21.56617722,0.84573244
amhara,debark_town,7/1/2024,0,21.83333333,24.01180265,1.099777221
amhara,debark_town,8/1/2024,0,19.33333333,25.59427019,1.323841562
amhara,debark_town,9/1/2024,0,16.33333333,26.80795902,1.641303613
amhara,debark_town,10/1/2024,0,13.5,27.60978088,2.045168954
amhara,debark_town,11/1/2024,0,11.5,28.16913204,2.449489743
amhara,debark_town,12/1/2024,0,0,0,
amhara,janamora,1/1/2019,0,,,
amhara,janamora,2/1/2019,0,,,
amhara,janamora,3/1/2019,0,0,0,
amhara,janamora,4/1/2019,0,0,0,
amhara,janamora,5/1/2019,0,0,0,
amhara,janamora,6/1/2019,0,0,0,
amhara,janamora,7/1/2019,0,0,0,
amhara,janamora,8/1/2019,0,0,0,
amhara,janamora,9/1/2019,0,0,0,
amhara,janamora,10/1/2019,0,0,0,
amhara,janamora,11/1/2019,0,0,0,
amhara,janamora,12/1/2019,0,0,0,
amhara,janamora,1/1/2020,0,0,0,
amhara,janamora,2/1/2020,0,0,0,
amhara,janamora,3/1/2020,0,0,0,
amhara,janamora,4/1/2020,0,0,0,
amhara,janamora,5/1/2020,0,0,0,
amhara,janamora,6/1/2020,0,0,0,
amhara,janamora,7/1/2020,0,0,0,
amhara,janamora,8/1/2020,0,0,0,
amhara,janamora,9/1/2020,0,0,0,
amhara,janamora,10/1/2020,0,0,0,
amhara,janamora,11/1/2020,0,0,0,
amhara,janamora,12/1/2020,0,0,0,
amhara,janamora,1/1/2021,0,0,0,
amhara,janamora,2/1/2021,0,0,0,
amhara,janamora,3/1/2021,0,0,0,
amhara,janamora,4/1/2021,0,0,0,
amhara,janamora,5/1/2021,0,0,0,
amhara,janamora,6/1/2021,0,0,0,
amhara,janamora,7/1/2021,0,0,0,
amhara,janamora,8/1/2021,0,0,0,
amhara,janamora,9/1/2021,0,0,0,
amhara,janamora,10/1/2021,0,0,0,
amhara,janamora,11/1/2021,0,0,0,
amhara,janamora,12/1/2021,0,0,0,
amhara,janamora,1/1/2022,0,0,0,
amhara,janamora,2/1/2022,0,0,0,
amhara,janamora,3/1/2022,0,0,0,
amhara,janamora,4/1/2022,0,0,0,
amhara,janamora,5/1/2022,0,0,0,
amhara,janamora,6/1/2022,0,0,0,
amhara,janamora,7/1/2022,3044,507.3333333,1242.707796,2.449489743
amhara,janamora,8/1/2022,4135,1196.5,1885.443582,1.575799065
amhara,janamora,9/1/2022,3218,1732.833333,1934.084633,1.116140021
amhara,janamora,10/1/2022,3155,2258.666667,1792.442988,0.793584558
amhara,janamora,11/1/2022,1802,2559,1458.082851,0.569786186
amhara,janamora,12/1/2022,3808,3193.666667,803.0862137,0.251462127
amhara,janamora,1/1/2023,2537,3109.166667,847.4322195,0.272559277
amhara,janamora,2/1/2023,2985,2917.5,683.1359308,0.234151133
amhara,janamora,3/1/2023,2615,2817,674.3853498,0.23939842
amhara,janamora,4/1/2023,3145,2815.333333,673.3945847,0.239188226
amhara,janamora,5/1/2023,3933,3170.5,588.6893069,0.185677119
amhara,janamora,6/1/2023,3054,3044.833333,499.036839,0.163896274
amhara,janamora,7/1/2023,4533,3377.5,712.4509106,0.210940314
amhara,janamora,8/1/2023,3101,3396.833333,701.1540249,0.20641402
amhara,janamora,9/1/2023,4652,3736.333333,739.0133061,0.197791053
amhara,janamora,10/1/2023,4582,3975.833333,741.8920182,0.186600382
amhara,janamora,11/1/2023,3242,3860.666667,801.1386064,0.207513022
amhara,janamora,12/1/2023,2978,3848,816.8894662,0.212289362
amhara,janamora,1/1/2024,2298,3475.5,942.0487779,0.271054173
amhara,janamora,2/1/2024,2988,3456.666667,952.1089574,0.275441357
amhara,janamora,3/1/2024,1878,2994.333333,928.8069049,0.310188213
amhara,janamora,4/1/2024,2152,2589.333333,551.0174831,0.212802838
amhara,janamora,5/1/2024,1995,2381.5,487.0711447,0.204522841
amhara,janamora,6/1/2024,2684,2332.5,426.0233562,0.182646669
amhara,janamora,7/1/2024,0,1949.5,1045.630097,0.53635809
amhara,janamora,8/1/2024,0,1451.5,1157.648954,0.797553533
amhara,janamora,9/1/2024,0,1138.5,1267.903111,1.113661055
amhara,janamora,10/1/2024,0,779.8333333,1227.602609,1.574185864
amhara,janamora,11/1/2024,0,447.3333333,1095.738412,2.449489743
amhara,janamora,12/1/2024,0,0,0,
somali,east_imi,1/1/2019,0,,,
somali,east_imi,2/1/2019,0,,,
somali,east_imi,3/1/2019,0,0,0,
somali,east_imi,4/1/2019,0,0,0,
somali,east_imi,5/1/2019,0,0,0,
somali,east_imi,6/1/2019,0,0,0,
somali,east_imi,7/1/2019,0,0,0,
somali,east_imi,8/1/2019,0,0,0,
somali,east_imi,9/1/2019,0,0,0,
somali,east_imi,10/1/2019,0,0,0,
somali,east_imi,11/1/2019,0,0,0,
somali,east_imi,12/1/2019,0,0,0,
somali,east_imi,1/1/2020,0,0,0,
somali,east_imi,2/1/2020,0,0,0,
somali,east_imi,3/1/2020,0,0,0,
somali,east_imi,4/1/2020,0,0,0,
somali,east_imi,5/1/2020,0,0,0,
somali,east_imi,6/1/2020,0,0,0,
somali,east_imi,7/1/2020,0,0,0,
somali,east_imi,8/1/2020,0,0,0,
somali,east_imi,9/1/2020,0,0,0,
somali,east_imi,10/1/2020,0,0,0,
somali,east_imi,11/1/2020,0,0,0,
somali,east_imi,12/1/2020,0,0,0,
somali,east_imi,1/1/2021,0,0,0,
somali,east_imi,2/1/2021,0,0,0,
somali,east_imi,3/1/2021,0,0,0,
somali,east_imi,4/1/2021,0,0,0,
somali,east_imi,5/1/2021,0,0,0,
somali,east_imi,6/1/2021,0,0,0,
somali,east_imi,7/1/2021,0,0,0,
somali,east_imi,8/1/2021,0,0,0,
somali,east_imi,9/1/2021,0,0,0,
somali,east_imi,10/1/2021,0,0,0,
somali,east_imi,11/1/2021,0,0,0,
somali,east_imi,12/1/2021,0,0,0,
somali,east_imi,1/1/2022,0,0,0,
somali,east_imi,2/1/2022,0,0,0,
somali,east_imi,3/1/2022,0,0,0,
somali,east_imi,4/1/2022,0,0,0,
somali,east_imi,5/1/2022,0,0,0,
somali,east_imi,6/1/2022,0,0,0,
somali,east_imi,7/1/2022,88,14.66666667,35.92584956,2.449489743
somali,east_imi,8/1/2022,52,23.33333333,37.89810901,1.624204672
somali,east_imi,9/1/2022,49,31.5,37.13623567,1.178928117
somali,east_imi,10/1/2022,66,42.5,35.68613176,0.839673688
somali,east_imi,11/1/2022,45,50,29.08607914,0.581721583
somali,east_imi,12/1/2022,73,62.16666667,16.55797894,0.266348187
somali,east_imi,1/1/2023,82,61.16666667,14.77046603,0.241479009
somali,east_imi,2/1/2023,0,52.5,29.31723043,0.558423437
somali,east_imi,3/1/2023,660,154.3333333,249.4479238,1.616293242
somali,east_imi,4/1/2023,279,189.8333333,249.5190707,1.314411259
somali,east_imi,5/1/2023,0,182.3333333,255.3512613,1.400463956
somali,east_imi,6/1/2023,0,170.1666667,263.2203766,1.546838648
somali,east_imi,7/1/2023,168,184.5,259.7781746,1.408011786
somali,east_imi,8/1/2023,144,208.5,245.5880697,1.17788043
somali,east_imi,9/1/2023,36,104.5,111.8709077,1.070535002
somali,east_imi,10/1/2023,145,82.16666667,78.45104631,0.954779468
somali,east_imi,11/1/2023,279,128.6666667,99.79111517,0.775578615
somali,east_imi,12/1/2023,277,174.8333333,92.1421004,0.52702822
somali,east_imi,1/1/2024,237,186.3333333,95.36805894,0.51181427
somali,east_imi,2/1/2024,182,192.6666667,93.2323263,0.483904808
somali,east_imi,3/1/2024,30,191.6666667,95.25894534,0.497003193
somali,east_imi,4/1/2024,241,207.6666667,93.90562638,0.452194028
somali,east_imi,5/1/2024,133,183.3333333,90.58182305,0.494082671
somali,east_imi,6/1/2024,20,140.5,97.8994382,0.696793154
somali,east_imi,7/1/2024,0,101,98.98282679,0.980027988
somali,east_imi,8/1/2024,0,70.66666667,97.0642399,1.373550565
somali,east_imi,9/1/2024,0,65.66666667,100.2968926,1.527363847
somali,east_imi,10/1/2024,0,25.5,53.26818938,2.088948603
somali,east_imi,11/1/2024,0,3.333333333,8.164965809,2.449489743
somali,east_imi,12/1/2024,0,0,0,
somali,west_imi,1/1/2019,0,,,
somali,west_imi,2/1/2019,0,,,
somali,west_imi,3/1/2019,0,0,0,
somali,west_imi,4/1/2019,0,0,0,
somali,west_imi,5/1/2019,0,0,0,
somali,west_imi,6/1/2019,0,0,0,
somali,west_imi,7/1/2019,0,0,0,
somali,west_imi,8/1/2019,0,0,0,
somali,west_imi,9/1/2019,0,0,0,
somali,west_imi,10/1/2019,0,0,0,
somali,west_imi,11/1/2019,0,0,0,
somali,west_imi,12/1/2019,0,0,0,
somali,west_imi,1/1/2020,0,0,0,
somali,west_imi,2/1/2020,0,0,0,
somali,west_imi,3/1/2020,0,0,0,
somali,west_imi,4/1/2020,0,0,0,
somali,west_imi,5/1/2020,0,0,0,
somali,west_imi,6/1/2020,0,0,0,
somali,west_imi,7/1/2020,0,0,0,
somali,west_imi,8/1/2020,0,0,0,
somali,west_imi,9/1/2020,0,0,0,
somali,west_imi,10/1/2020,0,0,0,
somali,west_imi,11/1/2020,0,0,0,
somali,west_imi,12/1/2020,0,0,0,
somali,west_imi,1/1/2021,0,0,0,
somali,west_imi,2/1/2021,0,0,0,
somali,west_imi,3/1/2021,0,0,0,
somali,west_imi,4/1/2021,0,0,0,
somali,west_imi,5/1/2021,0,0,0,
somali,west_imi,6/1/2021,0,0,0,
somali,west_imi,7/1/2021,0,0,0,
somali,west_imi,8/1/2021,0,0,0,
somali,west_imi,9/1/2021,0,0,0,
somali,west_imi,10/1/2021,0,0,0,
somali,west_imi,11/1/2021,0,0,0,
somali,west_imi,12/1/2021,0,0,0,
somali,west_imi,1/1/2022,0,0,0,
somali,west_imi,2/1/2022,0,0,0,
somali,west_imi,3/1/2022,0,0,0,
somali,west_imi,4/1/2022,0,0,0,
somali,west_imi,5/1/2022,0,0,0,
somali,west_imi,6/1/2022,0,0,0,
somali,west_imi,7/1/2022,336,56,137.1714256,2.449489743
somali,west_imi,8/1/2022,432,128,200.6070786,1.567242802
somali,west_imi,9/1/2022,309,179.5,200.8379944,1.118874621
somali,west_imi,10/1/2022,319,232.6666667,185.4504426,0.79706494
somali,west_imi,11/1/2022,473,311.5,166.3114548,0.533905152
somali,west_imi,12/1/2022,68,322.8333333,141.2705442,0.437595904
somali,west_imi,1/1/2023,271,312,142.5454314,0.456876383
somali,west_imi,2/1/2023,480,320,151.6812447,0.47400389
somali,west_imi,3/1/2023,312,320.5,151.6426721,0.473144063
somali,west_imi,4/1/2023,138,290.3333333,169.0096644,0.58212284
somali,west_imi,5/1/2023,84,225.5,159.2529435,0.706221479
somali,west_imi,6/1/2023,117,233.6666667,150.5810966,0.644426947
somali,west_imi,7/1/2023,260,231.8333333,150.1018543,0.647455878
somali,west_imi,8/1/2023,151,177,88.94942383,0.502539118
somali,west_imi,9/1/2023,113,143.8333333,61.36910189,0.426668148
somali,west_imi,10/1/2023,70,132.5,68.52371852,0.51716014
somali,west_imi,11/1/2023,228,156.5,73.19767756,0.46771679
somali,west_imi,12/1/2023,99,153.5,75.47383653,0.491686231
somali,west_imi,1/1/2024,235,149.3333333,68.81472711,0.460812905
somali,west_imi,2/1/2024,685,238.3333333,229.3849748,0.96245444
somali,west_imi,3/1/2024,112,238.1666667,229.4945896,0.9635882
somali,west_imi,4/1/2024,202,260.1666667,216.0846285,0.830562313
somali,west_imi,5/1/2024,135,244.6666667,222.1050802,0.907786431
somali,west_imi,6/1/2024,98,244.5,222.2365856,0.908943091
somali,west_imi,7/1/2024,0,205.3333333,243.8980661,1.187815257
somali,west_imi,8/1/2024,0,91.16666667,79.13132544,0.867985288
somali,west_imi,9/1/2024,0,72.5,86.13419762,1.188057898
somali,west_imi,10/1/2024,0,38.83333333,61.28757351,1.578220777
somali,west_imi,11/1/2024,0,16.33333333,40.00833247,2.449489743
somali,west_imi,12/1/2024,0,0,0,
"""

# ------------------------------------------------------------
# Parse the embedded CSV
df = pd.read_csv(io.StringIO(CSV_DATA))
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"]).copy()

# ------------------------------------------------------------
# Sidebar filters
st.sidebar.header("Filters")
regions = ["All"] + sorted(df["region"].dropna().unique().tolist())
region_sel = st.sidebar.selectbox("Region", regions, index=0)

if region_sel == "All":
    woptions = ["All"] + sorted(df["woreda"].dropna().unique().tolist())
else:
    woptions = ["All"] + sorted(df.loc[df["region"] == region_sel, "woreda"].dropna().unique().tolist())
woreda_sel = st.sidebar.selectbox("Woreda", woptions, index=0)

# Date range inputs using date_input (robust, avoids Timestamp in slider)
date_min = df["date"].min().date()
date_max = df["date"].max().date()
st.sidebar.markdown("### Date range")
date_left = st.sidebar.date_input("Start date", value=date_min, min_value=date_min, max_value=date_max)
date_right = st.sidebar.date_input("End date", value=date_max, min_value=date_min, max_value=date_max)
if date_left > date_right:
    date_left, date_right = date_right, date_left
df["date_only"] = df["date"].dt.date

# Apply filters
mask = (df["date_only"] >= date_left) & (df["date_only"] <= date_right)
if region_sel != "All":
    mask &= (df["region"] == region_sel)
if woreda_sel != "All":
    mask &= (df["woreda"] == woreda_sel)
df_filt = df.loc[mask].copy()

# ------------------------------------------------------------
# KPIs
st.markdown("#### Overview")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Records", str(len(df_filt)))
with c2:
    total_cases = int(df_filt["acute_cases"].fillna(0).sum())
    st.metric("Total acute cases", f"{total_cases:,}")
with c3:
    st.metric("Regions", str(df_filt["region"].nunique()))
with c4:
    st.metric("Woredas", str(df_filt["woreda"].nunique()))

st.markdown("---")

# ------------------------------------------------------------
# Time series: acute cases
st.subheader("Acute cases over time")
if not df_filt.empty:
    ts_chart = alt.Chart(df_filt).mark_line(point=True, color=AAH_BLUE).encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("acute_cases:Q", title="Acute cases"),
        color=alt.Color("woreda:N", title="Woreda"),
        tooltip=["region","woreda","date:T","acute_cases:Q"]
    ).properties(height=300)
    st.altair_chart(ts_chart, use_container_width=True)
else:
    st.info("No data for the selected filters and date range.")

# ------------------------------------------------------------
# Heatmap options
st.subheader("Heatmap views")
st.caption("Choose either a geographic bubble heatmap (approximate centroids) or a matrix heatmap.")

# 1) Geographic bubble heatmap (approximate woreda centroids — embedded, no external files)
# Coordinates dictionary (approximate centroids for featured woredas)
woreda_coords = {
    # Amhara (Simien area approximations)
    "beyeda": {"lat": 13.31, "lon": 38.42},
    "debark_town": {"lat": 13.15, "lon": 37.90},
    "janamora": {"lat": 13.25, "lon": 38.15},
    # Somali (Imi area approximations)
    "east_imi": {"lat": 6.48, "lon": 42.19},
    "west_imi": {"lat": 6.25, "lon": 42.62},
}

geo_df = (
    df_filt.groupby(["region","woreda"], as_index=False)["acute_cases"].sum()
    .assign(lat=lambda d: d["woreda"].map(lambda w: woreda_coords.get(str(w).lower(), {}).get("lat", math.nan)),
            lon=lambda d: d["woreda"].map(lambda w: woreda_coords.get(str(w).lower(), {}).get("lon", math.nan)))
)

st.markdown("##### Geographic bubble heatmap (embedded centroids)")
if geo_df[["lat","lon"]].dropna().empty:
    st.caption("No coordinates available for selected woredas.")
else:
    bubble = alt.Chart(geo_df.dropna(subset=["lat","lon"])).mark_circle().encode(
        longitude="lon:Q",
        latitude="lat:Q",
        size=alt.Size("acute_cases:Q", title="Acute cases", scale=alt.Scale(range=[100, 3000])),
        color=alt.Color("region:N", scale=alt.Scale(range=[AAH_BLUE, AAH_ORANGE, AAH_GREEN])),
        tooltip=["region","woreda","acute_cases:Q"]
    ).project(type="mercator").properties(height=420)
    st.altair_chart(bubble, use_container_width=True)

# 2) Matrix heatmap (Region × Woreda intensity)
st.markdown("##### Matrix heatmap (region × woreda)")
mat_df = df_filt.groupby(["region","woreda"], as_index=False)["acute_cases"].sum()
if mat_df.empty:
    st.caption("No data to show.")
else:
    matrix = alt.Chart(mat_df).mark_rect().encode(
        x=alt.X("woreda:N", title="Woreda"),
        y=alt.Y("region:N", title="Region"),
        color=alt.Color("acute_cases:Q", title="Acute cases", scale=alt.Scale(scheme="oranges")),
        tooltip=["region","woreda","acute_cases:Q"]
    ).properties(height=260)
    st.altair_chart(matrix, use_container_width=True)

st.markdown("---")

# ------------------------------------------------------------
# Data table and download
st.subheader("Filtered data")
st.dataframe(df_filt.drop(columns=["date_only"]), use_container_width=True)

st.download_button(
    "Download filtered CSV",
    data=df_filt.drop(columns=["date_only"]).to_csv(index=False),
    file_name="filtered_summary_forecast.csv",
    mime="text/csv"
)

# ------------------------------------------------------------
# Footer
st.markdown(
    f"""
    <div style="text-align:center; color:{AAH_GREY}; font-size:0.9em; margin-top:16px;">
        © Action Against Hunger – Ethiopia Dashboard
    </div>
    """,
    unsafe_allow_html=True
)

#  python -m streamlit run acf_forecast_dashboard.py
# cd "D:/VS/ethiopia_gam_dashboard"  