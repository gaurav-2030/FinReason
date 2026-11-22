# TRACE replay

Weights selected on dev (finqa_dev_n50, tatqa_dev_n50): {'w_flagged': 0.0, 'w_soft': 0.0, 'w_text': 0.5} -> mean dev accuracy 0.700

| run                                | variant                                       |   n |   accuracy |   tokens_per_q |   calls_per_q |   early_exit_rate |   accuracy_early |
|:-----------------------------------|:----------------------------------------------|----:|-----------:|---------------:|--------------:|------------------:|-----------------:|
| finqa_dev_n50 (dev)                | TRACE (full)                                  |  50 |      0.620 |      20407.220 |         6.220 |             0.000 |          nan     |
| finqa_dev_n50 (dev)                | TRACE adaptive                                |  50 |      0.620 |      14833.540 |         4.440 |             0.440 |            0.818 |
| finqa_dev_n50 (dev)                | - repair                                      |  50 |      0.620 |      19644.280 |         6.000 |             0.000 |          nan     |
| finqa_dev_n50 (dev)                | - cell-level audit (v1+v2 checks only)        |  50 |      0.600 |      19952.440 |         6.100 |             0.000 |          nan     |
| finqa_dev_n50 (dev)                | - audit entirely (no filter, no repair)       |  50 |      0.600 |      19644.280 |         6.000 |             0.000 |          nan     |
| finqa_dev_n50 (dev)                | - text views (programs only)                  |  50 |      0.560 |      11850.180 |         3.220 |             0.000 |          nan     |
| finqa_dev_n50 (dev)                | - decomposition view                          |  50 |      0.600 |      17408.860 |         5.220 |             0.000 |          nan     |
| finqa_dev_n50 (dev)                | - view diversity (guided programs + CoT only) |  50 |      0.580 |      14508.240 |         4.080 |             0.000 |          nan     |
| finqa_dev_n50 (dev)                | - ans fix                                     |  50 |      0.620 |      20407.220 |         6.220 |             0.000 |          nan     |
| tatqa_dev_n50 (dev)                | TRACE (full)                                  |  50 |      0.780 |      17400.060 |         6.080 |             0.000 |          nan     |
| tatqa_dev_n50 (dev)                | TRACE adaptive                                |  50 |      0.780 |       9157.580 |         3.020 |             0.760 |            0.816 |
| tatqa_dev_n50 (dev)                | - repair                                      |  50 |      0.780 |      17139.720 |         6.000 |             0.000 |          nan     |
| tatqa_dev_n50 (dev)                | - cell-level audit (v1+v2 checks only)        |  50 |      0.760 |      17139.720 |         6.000 |             0.000 |          nan     |
| tatqa_dev_n50 (dev)                | - audit entirely (no filter, no repair)       |  50 |      0.760 |      17139.720 |         6.000 |             0.000 |          nan     |
| tatqa_dev_n50 (dev)                | - text views (programs only)                  |  50 |      0.760 |      10110.780 |         3.080 |             0.000 |          nan     |
| tatqa_dev_n50 (dev)                | - decomposition view                          |  50 |      0.780 |      14809.480 |         5.080 |             0.000 |          nan     |
| tatqa_dev_n50 (dev)                | - view diversity (guided programs + CoT only) |  50 |      0.760 |      12607.560 |         4.040 |             0.000 |          nan     |
| tatqa_dev_n50 (dev)                | - ans fix                                     |  50 |      0.780 |      17400.060 |         6.080 |             0.000 |          nan     |
| finqa_test_n100__ollama-qwen3-1.7b | TRACE (full)                                  | 100 |      0.610 |      20168.960 |         6.210 |             0.000 |          nan     |
| finqa_test_n100__ollama-qwen3-1.7b | TRACE adaptive                                | 100 |      0.610 |      14716.860 |         4.400 |             0.450 |            0.756 |
| finqa_test_n100__ollama-qwen3-1.7b | - repair                                      | 100 |      0.610 |      19418.670 |         6.000 |             0.000 |          nan     |
| finqa_test_n100__ollama-qwen3-1.7b | - cell-level audit (v1+v2 checks only)        | 100 |      0.620 |      19836.830 |         6.110 |             0.000 |          nan     |
| finqa_test_n100__ollama-qwen3-1.7b | - audit entirely (no filter, no repair)       | 100 |      0.590 |      19418.670 |         6.000 |             0.000 |          nan     |
| finqa_test_n100__ollama-qwen3-1.7b | - text views (programs only)                  | 100 |      0.540 |      11708.610 |         3.210 |             0.000 |          nan     |
| finqa_test_n100__ollama-qwen3-1.7b | - decomposition view                          | 100 |      0.610 |      17200.880 |         5.210 |             0.000 |          nan     |
| finqa_test_n100__ollama-qwen3-1.7b | - view diversity (guided programs + CoT only) | 100 |      0.540 |      14419.660 |         4.100 |             0.000 |          nan     |
| finqa_test_n100__ollama-qwen3-1.7b | - ans fix                                     | 100 |      0.610 |      20168.960 |         6.210 |             0.000 |          nan     |
| tatqa_test_n100__ollama-qwen3-1.7b | TRACE (full)                                  | 100 |      0.810 |      17535.120 |         6.180 |             0.000 |          nan     |
| tatqa_test_n100__ollama-qwen3-1.7b | TRACE adaptive                                | 100 |      0.810 |       9736.580 |         3.270 |             0.720 |            0.903 |
| tatqa_test_n100__ollama-qwen3-1.7b | - repair                                      | 100 |      0.810 |      16959.350 |         6.000 |             0.000 |          nan     |
| tatqa_test_n100__ollama-qwen3-1.7b | - cell-level audit (v1+v2 checks only)        | 100 |      0.810 |      17017.730 |         6.020 |             0.000 |          nan     |
| tatqa_test_n100__ollama-qwen3-1.7b | - audit entirely (no filter, no repair)       | 100 |      0.810 |      16959.350 |         6.000 |             0.000 |          nan     |
| tatqa_test_n100__ollama-qwen3-1.7b | - text views (programs only)                  | 100 |      0.790 |      10337.430 |         3.180 |             0.000 |          nan     |
| tatqa_test_n100__ollama-qwen3-1.7b | - decomposition view                          | 100 |      0.800 |      14975.560 |         5.180 |             0.000 |          nan     |
| tatqa_test_n100__ollama-qwen3-1.7b | - view diversity (guided programs + CoT only) | 100 |      0.780 |      12654.340 |         4.080 |             0.000 |          nan     |
| tatqa_test_n100__ollama-qwen3-1.7b | - ans fix                                     | 100 |      0.810 |      17535.120 |         6.180 |             0.000 |          nan     |


| run                                | method   |   accuracy |   aurc |   acc_at_50 |   acc_at_80 |   oracle |
|:-----------------------------------|:---------|-----------:|-------:|------------:|------------:|---------:|
| finqa_dev_n50 (dev)                | TRACE    |      0.620 |  0.262 |       0.800 |       0.700 |    0.700 |
| tatqa_dev_n50 (dev)                | TRACE    |      0.780 |  0.248 |       0.840 |       0.825 |    0.840 |
| finqa_test_n100__ollama-qwen3-1.7b | TRACE    |      0.610 |  0.203 |       0.800 |       0.713 |    0.750 |
| tatqa_test_n100__ollama-qwen3-1.7b | TRACE    |      0.810 |  0.103 |       0.920 |       0.875 |    0.900 |
