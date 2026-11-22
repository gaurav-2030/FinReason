# FinReason results

## Summary of all runs

| dataset   | perturbed   | model             | fmt      | context   | think   | strategy                                             |   n |   accuracy |   ci_low |   ci_high |   accuracy_1pct |   exact_match |    f1 |   format_failure |   code_failure |   calls |   total_tokens |   tokens_per_correct |   latency_s |
|:----------|:------------|:------------------|:---------|:----------|:--------|:-----------------------------------------------------|----:|-----------:|---------:|----------:|----------------:|--------------:|------:|-----------------:|---------------:|--------:|---------------:|---------------------:|------------:|
| finqa     | False       | ollama:qwen3:1.7b | html     | full      | False   | cot_fs                                               | 100 |      0.490 |    0.400 |     0.590 |           0.510 |         0.310 | 0.310 |            0.000 |          0.000 |   1.000 |       3039.040 |             6202.122 |      14.578 |
| finqa     | False       | ollama:qwen3:1.7b | json     | full      | False   | cot_fs                                               | 100 |      0.540 |    0.440 |     0.640 |           0.580 |         0.310 | 0.310 |            0.030 |          0.000 |   1.000 |       3064.580 |             5675.148 |      16.920 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | direct                                               | 100 |      0.050 |    0.010 |     0.100 |           0.050 |         0.030 | 0.030 |            0.010 |          0.000 |   1.000 |       1147.830 |            22956.600 |       6.635 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | cot_zs                                               | 100 |      0.490 |    0.390 |     0.580 |           0.530 |         0.310 | 0.310 |            0.070 |          0.000 |   1.000 |       1281.100 |             2614.490 |      11.271 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | cot_fs                                               | 100 |      0.520 |    0.420 |     0.620 |           0.550 |         0.320 | 0.320 |            0.020 |          0.000 |   1.000 |       2744.880 |             5278.615 |      21.393 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | decomp_fs                                            | 100 |      0.440 |    0.340 |     0.540 |           0.520 |         0.280 | 0.280 |            0.000 |          0.000 |   1.000 |       2968.080 |             6745.636 |      22.259 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | pot_fs                                               | 100 |      0.570 |    0.470 |     0.660 |           0.570 |         0.560 | 0.550 |            0.000 |          0.000 |   1.010 |       2498.340 |             4383.053 |      15.406 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | sc_cot                                               | 100 |      0.510 |    0.420 |     0.610 |           0.540 |         0.310 | 0.310 |            0.000 |          0.000 |   5.000 |      13720.470 |            26902.882 |      72.911 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | pot_sc                                               | 100 |      0.560 |    0.460 |     0.660 |           0.560 |         0.550 | 0.540 |            0.000 |          0.010 |   5.000 |      12387.810 |            22121.089 |      52.979 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | vpsc                                                 | 100 |      0.560 |    0.460 |     0.660 |           0.560 |         0.550 | 0.540 |            0.000 |          0.010 |   5.000 |      12387.810 |            22121.089 |      52.979 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | dspy:artifacts/dspy_bootstrap_ollama-qwen3-1.7b.json | 100 |      0.450 |    0.350 |     0.550 |           0.530 |         0.290 | 0.290 |            0.010 |          0.000 |   1.000 |       5145.150 |            11433.667 |      24.466 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json   | 100 |      0.430 |    0.340 |     0.530 |           0.470 |         0.270 | 0.270 |            0.100 |          0.000 |   1.000 |       1950.220 |             4535.395 |      23.651 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | True    | cot_zs                                               | 100 |      0.630 |    0.530 |     0.730 |           0.640 |         0.450 | 0.450 |            0.030 |          0.000 |   1.000 |       2546.610 |             4042.238 |     151.459 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | retrieved | False   | pot_fs                                               | 100 |      0.510 |    0.410 |     0.610 |           0.520 |         0.500 | 0.500 |            0.010 |          0.010 |   1.010 |       1812.250 |             3553.431 |       7.805 |
| finqa     | False       | ollama:qwen3:1.7b | text     | full      | False   | cot_fs                                               | 100 |      0.440 |    0.350 |     0.540 |           0.480 |         0.270 | 0.270 |            0.070 |          0.000 |   1.000 |       2917.930 |             6631.659 |      16.098 |
| finqa     | False       | ollama:qwen3:8b   | markdown | full      | False   | direct                                               | 100 |      0.370 |    0.280 |     0.470 |           0.410 |         0.260 | 0.260 |            0.040 |          0.000 |   1.000 |       1183.490 |             3198.622 |      54.071 |
| finqa     | False       | ollama:qwen3:8b   | markdown | full      | False   | cot_zs                                               | 100 |      0.750 |    0.660 |     0.830 |           0.770 |         0.620 | 0.620 |            0.000 |          0.000 |   1.000 |       1279.270 |             1705.693 |      73.582 |
| finqa     | False       | ollama:qwen3:8b   | markdown | full      | False   | cot_fs                                               | 100 |      0.700 |    0.600 |     0.790 |           0.710 |         0.560 | 0.560 |            0.010 |          0.000 |   1.000 |       2754.440 |             3934.914 |      60.750 |
| finqa     | False       | ollama:qwen3:8b   | markdown | full      | False   | decomp_fs                                            | 100 |      0.730 |    0.640 |     0.820 |           0.740 |         0.660 | 0.660 |            0.010 |          0.000 |   1.000 |       2961.280 |             4056.548 |      67.064 |
| finqa     | False       | ollama:qwen3:8b   | markdown | full      | False   | pot_fs                                               | 100 |      0.730 |    0.640 |     0.820 |           0.730 |         0.720 | 0.720 |            0.000 |          0.000 |   1.000 |       2485.200 |             3404.384 |      71.835 |
| finqa     | False       | ollama:qwen3:8b   | markdown | full      | False   | sc_cot                                               | 100 |      0.730 |    0.640 |     0.820 |           0.730 |         0.590 | 0.590 |            0.000 |          0.000 |   5.000 |      13756.770 |            18844.890 |     201.104 |
| finqa     | True        | ollama:qwen3:1.7b | markdown | full      | False   | cot_fs                                               |  88 |      0.500 |    0.398 |     0.602 |           0.523 |         0.239 | 0.239 |            0.011 |          0.000 |   1.000 |       2737.114 |             5474.227 |      14.252 |
| finqa     | True        | ollama:qwen3:1.7b | markdown | full      | False   | pot_fs                                               |  88 |      0.557 |    0.455 |     0.659 |           0.557 |         0.557 | 0.557 |            0.000 |          0.000 |   1.023 |       2525.898 |             4536.306 |      14.575 |
| finqa     | True        | ollama:qwen3:1.7b | markdown | full      | False   | vpsc                                                 |  88 |      0.545 |    0.443 |     0.648 |           0.545 |         0.545 | 0.545 |            0.000 |          0.011 |   5.000 |      12351.011 |            22643.521 |      45.185 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | direct                                               |  44 |      0.023 |    0.000 |     0.068 |           0.068 |         0.023 | 0.023 |            0.023 |          0.000 |   1.000 |        739.545 |            32540.000 |       6.947 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | cot_zs                                               |  44 |      0.659 |    0.523 |     0.795 |           0.727 |         0.318 | 0.318 |            0.000 |          0.000 |   1.000 |        861.068 |             1306.448 |      10.483 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | cot_fs                                               |  44 |      0.659 |    0.523 |     0.795 |           0.705 |         0.364 | 0.364 |            0.000 |          0.000 |   1.000 |       2323.614 |             3525.483 |       7.601 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | decomp_fs                                            |  44 |      0.659 |    0.523 |     0.795 |           0.705 |         0.273 | 0.273 |            0.000 |          0.000 |   1.000 |       2562.227 |             3887.517 |      11.329 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | pot_fs                                               |  44 |      0.773 |    0.636 |     0.886 |           0.773 |         0.773 | 0.773 |            0.000 |          0.000 |   1.000 |       2067.000 |             2674.941 |      10.910 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | sc_cot                                               |  44 |      0.659 |    0.523 |     0.795 |           0.705 |         0.386 | 0.386 |            0.000 |          0.000 |   5.000 |      11613.386 |            17620.310 |      32.993 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | pot_sc                                               |  44 |      0.773 |    0.659 |     0.886 |           0.773 |         0.773 | 0.773 |            0.000 |          0.000 |   5.000 |      10334.818 |            13374.471 |      49.879 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | vpsc                                                 |  44 |      0.773 |    0.636 |     0.886 |           0.773 |         0.773 | 0.773 |            0.000 |          0.000 |   5.000 |      10334.818 |            13374.471 |      49.879 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json   |  44 |      0.682 |    0.545 |     0.818 |           0.705 |         0.205 | 0.205 |            0.023 |          0.000 |   1.000 |       1528.614 |             2241.967 |      30.018 |
| tatqa     | False       | ollama:qwen3:1.7b | html     | full      | False   | cot_fs                                               | 100 |      0.730 |    0.640 |     0.820 |           0.750 |         0.540 | 0.540 |            0.010 |          0.000 |   1.000 |       2642.840 |             3620.329 |      11.382 |
| tatqa     | False       | ollama:qwen3:1.7b | json     | full      | False   | cot_fs                                               | 100 |      0.680 |    0.580 |     0.770 |           0.710 |         0.460 | 0.460 |            0.000 |          0.000 |   1.000 |       2676.180 |             3935.559 |      11.797 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | direct                                               | 100 |      0.110 |    0.050 |     0.170 |           0.110 |         0.080 | 0.080 |            0.050 |          0.000 |   1.000 |        801.740 |             7288.545 |      13.308 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | cot_zs                                               | 100 |      0.680 |    0.590 |     0.770 |           0.710 |         0.460 | 0.460 |            0.030 |          0.000 |   1.000 |        856.070 |             1258.926 |      16.175 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | cot_fs                                               | 100 |      0.730 |    0.640 |     0.810 |           0.760 |         0.520 | 0.520 |            0.010 |          0.000 |   1.000 |       2319.340 |             3177.178 |      15.172 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | decomp_fs                                            | 100 |      0.700 |    0.610 |     0.790 |           0.720 |         0.490 | 0.490 |            0.010 |          0.000 |   1.000 |       2559.560 |             3656.514 |      15.763 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | pot_fs                                               | 100 |      0.670 |    0.580 |     0.760 |           0.670 |         0.660 | 0.660 |            0.000 |          0.000 |   1.020 |       2134.760 |             3186.209 |      11.073 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | sc_cot                                               | 100 |      0.740 |    0.650 |     0.820 |           0.770 |         0.530 | 0.530 |            0.000 |          0.000 |   5.000 |      11593.200 |            15666.486 |      51.726 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | pot_sc                                               | 100 |      0.670 |    0.580 |     0.760 |           0.670 |         0.660 | 0.660 |            0.000 |          0.010 |   5.000 |      10382.350 |            15496.045 |      43.450 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | vpsc                                                 | 100 |      0.670 |    0.570 |     0.760 |           0.670 |         0.660 | 0.660 |            0.000 |          0.010 |   5.000 |      10382.350 |            15496.045 |      43.450 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json   | 100 |      0.600 |    0.510 |     0.690 |           0.620 |         0.370 | 0.370 |            0.020 |          0.000 |   1.000 |       1558.590 |             2597.650 |      25.266 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | retrieved | False   | pot_fs                                               | 100 |      0.560 |    0.460 |     0.660 |           0.560 |         0.550 | 0.550 |            0.000 |          0.000 |   1.000 |       1797.400 |             3209.643 |       7.416 |
| tatqa     | False       | ollama:qwen3:1.7b | text     | full      | False   | cot_fs                                               | 100 |      0.630 |    0.530 |     0.720 |           0.660 |         0.450 | 0.450 |            0.010 |          0.000 |   1.000 |       2499.900 |             3968.095 |      11.172 |
| tatqa     | False       | ollama:qwen3:8b   | markdown | full      | False   | direct                                               |  59 |      0.390 |    0.271 |     0.508 |           0.458 |         0.271 | 0.271 |            0.000 |          0.000 |   1.000 |        708.034 |             1816.261 |      29.312 |

## McNemar tests against few-shot CoT (Holm-adjusted)

| dataset   | perturbed   | model             | fmt      | context   | think   | strategy                                             |   n |   accuracy |   baseline |   wins |   losses |   p_value |   p_holm |
|:----------|:------------|:------------------|:---------|:----------|:--------|:-----------------------------------------------------|----:|-----------:|-----------:|-------:|---------:|----------:|---------:|
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | cot_zs                                               | 100 |      0.490 |      0.520 |     14 |       17 |     0.720 |    1.000 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | decomp_fs                                            | 100 |      0.440 |      0.520 |      7 |       15 |     0.134 |    1.000 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | direct                                               | 100 |      0.050 |      0.520 |      1 |       48 |     0.000 |    0.000 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | dspy:artifacts/dspy_bootstrap_ollama-qwen3-1.7b.json | 100 |      0.450 |      0.520 |     10 |       17 |     0.248 |    1.000 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | pot_fs                                               | 100 |      0.570 |      0.520 |     14 |        9 |     0.405 |    1.000 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | pot_sc                                               | 100 |      0.560 |      0.520 |     14 |       10 |     0.541 |    1.000 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | sc_cot                                               | 100 |      0.510 |      0.520 |      1 |        2 |     1.000 |    1.000 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json   | 100 |      0.430 |      0.520 |     10 |       19 |     0.136 |    1.000 |
| finqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | vpsc                                                 | 100 |      0.560 |      0.520 |     14 |       10 |     0.541 |    1.000 |
| finqa     | False       | ollama:qwen3:8b   | markdown | full      | False   | cot_zs                                               | 100 |      0.750 |      0.700 |     15 |       10 |     0.424 |    1.000 |
| finqa     | False       | ollama:qwen3:8b   | markdown | full      | False   | decomp_fs                                            | 100 |      0.730 |      0.700 |     13 |       10 |     0.678 |    1.000 |
| finqa     | False       | ollama:qwen3:8b   | markdown | full      | False   | direct                                               | 100 |      0.370 |      0.700 |      4 |       37 |     0.000 |    0.000 |
| finqa     | False       | ollama:qwen3:8b   | markdown | full      | False   | pot_fs                                               | 100 |      0.730 |      0.700 |     11 |        8 |     0.648 |    1.000 |
| finqa     | False       | ollama:qwen3:8b   | markdown | full      | False   | sc_cot                                               | 100 |      0.730 |      0.700 |      3 |        0 |     0.250 |    1.000 |
| finqa     | True        | ollama:qwen3:1.7b | markdown | full      | False   | pot_fs                                               |  88 |      0.557 |      0.500 |     16 |       11 |     0.442 |    0.884 |
| finqa     | True        | ollama:qwen3:1.7b | markdown | full      | False   | vpsc                                                 |  88 |      0.545 |      0.500 |     15 |       11 |     0.557 |    0.884 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | cot_zs                                               |  44 |      0.659 |      0.659 |      6 |        6 |     1.000 |    1.000 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | decomp_fs                                            |  44 |      0.659 |      0.659 |      4 |        4 |     1.000 |    1.000 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | direct                                               |  44 |      0.023 |      0.659 |      0 |       28 |     0.000 |    0.000 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | pot_fs                                               |  44 |      0.773 |      0.659 |      9 |        4 |     0.267 |    1.000 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | pot_sc                                               |  44 |      0.773 |      0.659 |      9 |        4 |     0.267 |    1.000 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | sc_cot                                               |  44 |      0.659 |      0.659 |      0 |        0 |     1.000 |    1.000 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json   |  44 |      0.682 |      0.659 |      5 |        4 |     1.000 |    1.000 |
| indian    | False       | ollama:qwen3:1.7b | markdown | full      | False   | vpsc                                                 |  44 |      0.773 |      0.659 |      9 |        4 |     0.267 |    1.000 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | cot_zs                                               | 100 |      0.680 |      0.730 |      8 |       13 |     0.383 |    1.000 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | decomp_fs                                            | 100 |      0.700 |      0.730 |      9 |       12 |     0.664 |    1.000 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | direct                                               | 100 |      0.110 |      0.730 |      0 |       62 |     0.000 |    0.000 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | pot_fs                                               | 100 |      0.670 |      0.730 |     12 |       18 |     0.362 |    1.000 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | pot_sc                                               | 100 |      0.670 |      0.730 |     12 |       18 |     0.362 |    1.000 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | sc_cot                                               | 100 |      0.740 |      0.730 |      1 |        0 |     1.000 |    1.000 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json   | 100 |      0.600 |      0.730 |      9 |       22 |     0.029 |    0.206 |
| tatqa     | False       | ollama:qwen3:1.7b | markdown | full      | False   | vpsc                                                 | 100 |      0.670 |      0.730 |     12 |       18 |     0.362 |    1.000 |

## Accuracy by number of reasoning steps (main setting)

|                                                                                        |   1 step |   2 steps |   3+ steps |
|:---------------------------------------------------------------------------------------|---------:|----------:|-----------:|
| ('finqa', 'ollama:qwen3:1.7b', 'cot_fs')                                               |    0.574 |     0.500 |      0.000 |
| ('finqa', 'ollama:qwen3:1.7b', 'cot_zs')                                               |    0.443 |     0.618 |      0.200 |
| ('finqa', 'ollama:qwen3:1.7b', 'decomp_fs')                                            |    0.459 |     0.441 |      0.200 |
| ('finqa', 'ollama:qwen3:1.7b', 'direct')                                               |    0.082 |     0.000 |      0.000 |
| ('finqa', 'ollama:qwen3:1.7b', 'dspy:artifacts/dspy_bootstrap_ollama-qwen3-1.7b.json') |    0.426 |     0.529 |      0.200 |
| ('finqa', 'ollama:qwen3:1.7b', 'pot_fs')                                               |    0.557 |     0.647 |      0.200 |
| ('finqa', 'ollama:qwen3:1.7b', 'pot_sc')                                               |    0.557 |     0.618 |      0.200 |
| ('finqa', 'ollama:qwen3:1.7b', 'sc_cot')                                               |    0.557 |     0.500 |      0.000 |
| ('finqa', 'ollama:qwen3:1.7b', 'textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json')   |    0.393 |     0.529 |      0.200 |
| ('finqa', 'ollama:qwen3:1.7b', 'vpsc')                                                 |    0.557 |     0.618 |      0.200 |
| ('finqa', 'ollama:qwen3:8b', 'cot_fs')                                                 |    0.689 |     0.735 |      0.600 |
| ('finqa', 'ollama:qwen3:8b', 'cot_zs')                                                 |    0.770 |     0.706 |      0.800 |
| ('finqa', 'ollama:qwen3:8b', 'decomp_fs')                                              |    0.770 |     0.706 |      0.400 |
| ('finqa', 'ollama:qwen3:8b', 'direct')                                                 |    0.410 |     0.294 |      0.400 |
| ('finqa', 'ollama:qwen3:8b', 'pot_fs')                                                 |    0.738 |     0.735 |      0.600 |
| ('finqa', 'ollama:qwen3:8b', 'sc_cot')                                                 |    0.721 |     0.765 |      0.600 |
| ('indian', 'ollama:qwen3:1.7b', 'cot_fs')                                              |    0.600 |     0.692 |      0.688 |
| ('indian', 'ollama:qwen3:1.7b', 'cot_zs')                                              |    0.600 |     0.769 |      0.625 |
| ('indian', 'ollama:qwen3:1.7b', 'decomp_fs')                                           |    0.467 |     0.692 |      0.812 |
| ('indian', 'ollama:qwen3:1.7b', 'direct')                                              |    0.067 |     0.000 |      0.000 |
| ('indian', 'ollama:qwen3:1.7b', 'pot_fs')                                              |    0.800 |     0.769 |      0.750 |
| ('indian', 'ollama:qwen3:1.7b', 'pot_sc')                                              |    0.800 |     0.769 |      0.750 |
| ('indian', 'ollama:qwen3:1.7b', 'sc_cot')                                              |    0.600 |     0.692 |      0.688 |
| ('indian', 'ollama:qwen3:1.7b', 'textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json')  |    0.400 |     0.846 |      0.812 |
| ('indian', 'ollama:qwen3:1.7b', 'vpsc')                                                |    0.800 |     0.769 |      0.750 |
| ('tatqa', 'ollama:qwen3:1.7b', 'cot_fs')                                               |    0.800 |     0.688 |      0.667 |
| ('tatqa', 'ollama:qwen3:1.7b', 'cot_zs')                                               |    0.644 |     0.812 |      0.667 |
| ('tatqa', 'ollama:qwen3:1.7b', 'decomp_fs')                                            |    0.733 |     0.625 |      0.692 |
| ('tatqa', 'ollama:qwen3:1.7b', 'direct')                                               |    0.178 |     0.062 |      0.051 |
| ('tatqa', 'ollama:qwen3:1.7b', 'pot_fs')                                               |    0.600 |     0.562 |      0.795 |
| ('tatqa', 'ollama:qwen3:1.7b', 'pot_sc')                                               |    0.600 |     0.562 |      0.795 |
| ('tatqa', 'ollama:qwen3:1.7b', 'sc_cot')                                               |    0.800 |     0.750 |      0.667 |
| ('tatqa', 'ollama:qwen3:1.7b', 'textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json')   |    0.511 |     0.750 |      0.641 |
| ('tatqa', 'ollama:qwen3:1.7b', 'vpsc')                                                 |    0.600 |     0.562 |      0.795 |

## Accuracy by evidence source (main setting)

|                                                                                        |   table |   table-text |    text |
|:---------------------------------------------------------------------------------------|--------:|-------------:|--------:|
| ('finqa', 'ollama:qwen3:1.7b', 'cot_fs')                                               |   0.476 |        0.636 |   0.577 |
| ('finqa', 'ollama:qwen3:1.7b', 'cot_zs')                                               |   0.508 |        0.455 |   0.462 |
| ('finqa', 'ollama:qwen3:1.7b', 'decomp_fs')                                            |   0.429 |        0.364 |   0.500 |
| ('finqa', 'ollama:qwen3:1.7b', 'direct')                                               |   0.063 |        0.000 |   0.038 |
| ('finqa', 'ollama:qwen3:1.7b', 'dspy:artifacts/dspy_bootstrap_ollama-qwen3-1.7b.json') |   0.429 |        0.455 |   0.500 |
| ('finqa', 'ollama:qwen3:1.7b', 'pot_fs')                                               |   0.524 |        0.636 |   0.654 |
| ('finqa', 'ollama:qwen3:1.7b', 'pot_sc')                                               |   0.508 |        0.636 |   0.654 |
| ('finqa', 'ollama:qwen3:1.7b', 'sc_cot')                                               |   0.492 |        0.545 |   0.538 |
| ('finqa', 'ollama:qwen3:1.7b', 'textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json')   |   0.492 |        0.364 |   0.308 |
| ('finqa', 'ollama:qwen3:1.7b', 'vpsc')                                                 |   0.508 |        0.636 |   0.654 |
| ('finqa', 'ollama:qwen3:8b', 'cot_fs')                                                 |   0.698 |        0.636 |   0.731 |
| ('finqa', 'ollama:qwen3:8b', 'cot_zs')                                                 |   0.746 |        0.818 |   0.731 |
| ('finqa', 'ollama:qwen3:8b', 'decomp_fs')                                              |   0.762 |        0.727 |   0.654 |
| ('finqa', 'ollama:qwen3:8b', 'direct')                                                 |   0.429 |        0.182 |   0.308 |
| ('finqa', 'ollama:qwen3:8b', 'pot_fs')                                                 |   0.746 |        0.636 |   0.731 |
| ('finqa', 'ollama:qwen3:8b', 'sc_cot')                                                 |   0.730 |        0.727 |   0.731 |
| ('indian', 'ollama:qwen3:1.7b', 'cot_fs')                                              |   0.643 |        1.000 | nan     |
| ('indian', 'ollama:qwen3:1.7b', 'cot_zs')                                              |   0.690 |        0.000 | nan     |
| ('indian', 'ollama:qwen3:1.7b', 'decomp_fs')                                           |   0.643 |        1.000 | nan     |
| ('indian', 'ollama:qwen3:1.7b', 'direct')                                              |   0.024 |        0.000 | nan     |
| ('indian', 'ollama:qwen3:1.7b', 'pot_fs')                                              |   0.786 |        0.500 | nan     |
| ('indian', 'ollama:qwen3:1.7b', 'pot_sc')                                              |   0.786 |        0.500 | nan     |
| ('indian', 'ollama:qwen3:1.7b', 'sc_cot')                                              |   0.643 |        1.000 | nan     |
| ('indian', 'ollama:qwen3:1.7b', 'textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json')  |   0.667 |        1.000 | nan     |
| ('indian', 'ollama:qwen3:1.7b', 'vpsc')                                                |   0.786 |        0.500 | nan     |
| ('tatqa', 'ollama:qwen3:1.7b', 'cot_fs')                                               |   0.739 |        0.733 |   0.000 |
| ('tatqa', 'ollama:qwen3:1.7b', 'cot_zs')                                               |   0.725 |        0.567 |   1.000 |
| ('tatqa', 'ollama:qwen3:1.7b', 'decomp_fs')                                            |   0.725 |        0.633 |   1.000 |
| ('tatqa', 'ollama:qwen3:1.7b', 'direct')                                               |   0.116 |        0.100 |   0.000 |
| ('tatqa', 'ollama:qwen3:1.7b', 'pot_fs')                                               |   0.696 |        0.600 |   1.000 |
| ('tatqa', 'ollama:qwen3:1.7b', 'pot_sc')                                               |   0.696 |        0.600 |   1.000 |
| ('tatqa', 'ollama:qwen3:1.7b', 'sc_cot')                                               |   0.754 |        0.733 |   0.000 |
| ('tatqa', 'ollama:qwen3:1.7b', 'textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json')   |   0.594 |        0.600 |   1.000 |
| ('tatqa', 'ollama:qwen3:1.7b', 'vpsc')                                                 |   0.696 |        0.600 |   1.000 |

## Error taxonomy: counts of wrong answers (main setting)

|                                                                                        |   no_answer |   execution_error |   sign_error |   scale_error |   rounding_near_miss |   no_work_shown |   evidence_error |   reasoning_error |
|:---------------------------------------------------------------------------------------|------------:|------------------:|-------------:|--------------:|---------------------:|----------------:|-----------------:|------------------:|
| ('finqa', 'ollama:qwen3:1.7b', 'cot_fs')                                               |           0 |                 0 |            0 |             5 |                    3 |               0 |               31 |                 9 |
| ('finqa', 'ollama:qwen3:1.7b', 'cot_zs')                                               |           0 |                 0 |            5 |             6 |                    4 |               3 |               22 |                11 |
| ('finqa', 'ollama:qwen3:1.7b', 'decomp_fs')                                            |           0 |                 0 |            2 |            10 |                    2 |               0 |               30 |                12 |
| ('finqa', 'ollama:qwen3:1.7b', 'direct')                                               |           1 |                 0 |            0 |             0 |                    9 |              66 |               11 |                 8 |
| ('finqa', 'ollama:qwen3:1.7b', 'dspy:artifacts/dspy_bootstrap_ollama-qwen3-1.7b.json') |           1 |                 0 |            3 |             8 |                    3 |               0 |               30 |                10 |
| ('finqa', 'ollama:qwen3:1.7b', 'pot_fs')                                               |           0 |                 0 |            1 |             1 |                    1 |               0 |               34 |                 6 |
| ('finqa', 'ollama:qwen3:1.7b', 'pot_sc')                                               |           0 |                 1 |            1 |             1 |                    1 |               0 |               34 |                 6 |
| ('finqa', 'ollama:qwen3:1.7b', 'sc_cot')                                               |           0 |                 0 |            0 |             5 |                    3 |               0 |               31 |                10 |
| ('finqa', 'ollama:qwen3:1.7b', 'textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json')   |           0 |                 0 |            4 |             6 |                    3 |               0 |               26 |                18 |
| ('finqa', 'ollama:qwen3:1.7b', 'vpsc')                                                 |           0 |                 1 |            1 |             1 |                    1 |               0 |               34 |                 6 |
| ('finqa', 'ollama:qwen3:8b', 'cot_fs')                                                 |           0 |                 0 |            3 |             2 |                    2 |               1 |               11 |                11 |
| ('finqa', 'ollama:qwen3:8b', 'cot_zs')                                                 |           0 |                 0 |            2 |             4 |                    1 |               1 |                5 |                12 |
| ('finqa', 'ollama:qwen3:8b', 'decomp_fs')                                              |           0 |                 0 |            2 |             2 |                    6 |               1 |                8 |                 8 |
| ('finqa', 'ollama:qwen3:8b', 'direct')                                                 |           0 |                 0 |            0 |             6 |                    7 |              15 |               32 |                 3 |
| ('finqa', 'ollama:qwen3:8b', 'pot_fs')                                                 |           0 |                 0 |            3 |             2 |                    1 |               0 |               11 |                10 |
| ('finqa', 'ollama:qwen3:8b', 'sc_cot')                                                 |           0 |                 0 |            3 |             2 |                    1 |               1 |               11 |                 9 |
| ('indian', 'ollama:qwen3:1.7b', 'cot_fs')                                              |           0 |                 0 |            0 |             3 |                    1 |               0 |                4 |                 7 |
| ('indian', 'ollama:qwen3:1.7b', 'cot_zs')                                              |           0 |                 0 |            0 |             3 |                    2 |               0 |                4 |                 6 |
| ('indian', 'ollama:qwen3:1.7b', 'decomp_fs')                                           |           0 |                 0 |            0 |             3 |                    2 |               0 |                4 |                 6 |
| ('indian', 'ollama:qwen3:1.7b', 'direct')                                              |           1 |                 0 |            0 |             6 |                    2 |              32 |                1 |                 1 |
| ('indian', 'ollama:qwen3:1.7b', 'pot_fs')                                              |           0 |                 0 |            0 |             1 |                    2 |               0 |                6 |                 1 |
| ('indian', 'ollama:qwen3:1.7b', 'pot_sc')                                              |           0 |                 0 |            0 |             1 |                    2 |               0 |                6 |                 1 |
| ('indian', 'ollama:qwen3:1.7b', 'sc_cot')                                              |           0 |                 0 |            0 |             3 |                    1 |               0 |                4 |                 7 |
| ('indian', 'ollama:qwen3:1.7b', 'textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json')  |           0 |                 0 |            0 |             2 |                    0 |               0 |                6 |                 6 |
| ('indian', 'ollama:qwen3:1.7b', 'vpsc')                                                |           0 |                 0 |            0 |             1 |                    2 |               0 |                6 |                 1 |
| ('tatqa', 'ollama:qwen3:1.7b', 'cot_fs')                                               |           0 |                 0 |            1 |             5 |                    1 |               0 |               11 |                 9 |
| ('tatqa', 'ollama:qwen3:1.7b', 'cot_zs')                                               |           0 |                 0 |            4 |             5 |                    0 |               0 |               15 |                 8 |
| ('tatqa', 'ollama:qwen3:1.7b', 'decomp_fs')                                            |           0 |                 0 |            2 |             2 |                    0 |               0 |               20 |                 6 |
| ('tatqa', 'ollama:qwen3:1.7b', 'direct')                                               |           4 |                 0 |            8 |             1 |                    3 |              50 |               22 |                 1 |
| ('tatqa', 'ollama:qwen3:1.7b', 'pot_fs')                                               |           0 |                 0 |            2 |             1 |                    0 |               0 |               19 |                11 |
| ('tatqa', 'ollama:qwen3:1.7b', 'pot_sc')                                               |           0 |                 1 |            2 |             1 |                    0 |               0 |               18 |                11 |
| ('tatqa', 'ollama:qwen3:1.7b', 'sc_cot')                                               |           0 |                 0 |            1 |             5 |                    1 |               0 |               11 |                 8 |
| ('tatqa', 'ollama:qwen3:1.7b', 'textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json')   |           0 |                 0 |            5 |            10 |                    2 |               0 |               14 |                 9 |
| ('tatqa', 'ollama:qwen3:1.7b', 'vpsc')                                                 |           0 |                 1 |            2 |             1 |                    0 |               0 |               18 |                11 |

## Numerical perturbation test

| model             | strategy   |   n |   original_accuracy |   perturbed_accuracy |   drop |   only_original_right |   only_perturbed_right |   p_value |
|:------------------|:-----------|----:|--------------------:|---------------------:|-------:|----------------------:|-----------------------:|----------:|
| ollama:qwen3:1.7b | cot_fs     |  88 |               0.557 |                0.500 |  0.057 |                    15 |                     10 |     0.424 |
| ollama:qwen3:1.7b | pot_fs     |  88 |               0.580 |                0.557 |  0.023 |                     6 |                      4 |     0.754 |
| ollama:qwen3:1.7b | vpsc       |  88 |               0.568 |                0.545 |  0.023 |                     6 |                      4 |     0.754 |

## Ablations: table format, retrieval, thinking

|                                 |   format: markdown |   format: json |   format: html |   format: text |   PoT, full page |   PoT, retrieved top-5 |   zero-shot CoT, no thinking |   zero-shot CoT, thinking |
|:--------------------------------|-------------------:|---------------:|---------------:|---------------:|-----------------:|-----------------------:|-----------------------------:|--------------------------:|
| ('finqa', 'ollama:qwen3:1.7b')  |              0.520 |          0.540 |          0.490 |          0.440 |            0.570 |                  0.510 |                        0.490 |                     0.630 |
| ('finqa', 'ollama:qwen3:8b')    |              0.700 |        nan     |        nan     |        nan     |            0.730 |                nan     |                        0.750 |                   nan     |
| ('indian', 'ollama:qwen3:1.7b') |              0.659 |        nan     |        nan     |        nan     |            0.773 |                nan     |                        0.659 |                   nan     |
| ('tatqa', 'ollama:qwen3:1.7b')  |              0.730 |          0.680 |          0.730 |          0.630 |            0.670 |                  0.560 |                        0.680 |                   nan     |

## VPSC grounding diagnostics

| dataset   | model             |   questions |   vpsc_accuracy |   pot_sc_accuracy |   programs |   executed |   ungrounded |   flagged_questions |   flagged_wrong |   all_ungrounded |   answers_changed |   agreement |
|:----------|:------------------|------------:|----------------:|------------------:|-----------:|-----------:|-------------:|--------------------:|----------------:|-----------------:|------------------:|------------:|
| finqa     | ollama:qwen3:1.7b |         100 |           0.560 |             0.560 |        500 |        493 |           26 |                   6 |               6 |                5 |                 0 |       0.912 |
| indian    | ollama:qwen3:1.7b |          44 |           0.773 |             0.773 |        220 |        219 |            0 |                   0 |               0 |                0 |                 0 |       0.986 |
| tatqa     | ollama:qwen3:1.7b |         100 |           0.670 |             0.670 |        500 |        491 |            0 |                   0 |               0 |                0 |                 0 |       0.974 |

## One-time cost of automated optimization

| artifact                         | model             |   validation_accuracy |   minutes |   calls |   tokens |
|:---------------------------------|:------------------|----------------------:|----------:|--------:|---------:|
| dspy_bootstrap_ollama-qwen3-1.7b | ollama:qwen3:1.7b |                 0.425 |     2.517 |      15 |    23681 |
| textgrad_ollama-qwen3-1.7b       | ollama:qwen3:1.7b |                 0.625 |   317.550 |     382 |   767527 |
