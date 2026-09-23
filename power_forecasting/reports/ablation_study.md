# Ablation study

Positive improvement = lower error; negative = worse. Ratios below 1 are better. Weather comparisons keep learner, hyperparameters, folds and observation rows identical.

| comparison | MAE_before | MAE_after | ratio_after_before | absolute_improvement | relative_improvement_pct |
| --- | --- | --- | --- | --- | --- |
| LightGBM: ECMWF -> GFS | 0.16876 | 0.17571 | 1.04117 | -0.00695 | -4.11699 |
| LightGBM: ECMWF -> ICON | 0.16876 | 0.18878 | 1.11865 | -0.02002 | -11.86457 |
| LightGBM: ECMWF -> Simple | 0.16876 | 0.15645 | 0.92709 | 0.01230 | 7.29092 |
| LightGBM: ECMWF -> Weighted | 0.16876 | 0.16002 | 0.94821 | 0.00874 | 5.17866 |
| LightGBM: Weighted -> All | 0.16002 | 0.15741 | 0.98370 | 0.00261 | 1.62988 |
| LightGBM: All -> All_Disagreement | 0.15741 | 0.15783 | 1.00267 | -0.00042 | -0.26711 |
| LightGBM: Full_No_Performance -> Full | 0.15499 | 0.15653 | 1.00997 | -0.00155 | -0.99722 |
| LightGBM__Top15__global__default -> horizon | 0.15054 | 0.15173 | 1.00787 | -0.00119 | -0.78745 |
| LightGBM__Top15__global__default -> turbine | 0.15054 | 0.15058 | 1.00022 | -0.00003 | -0.02228 |
| LightGBM__Top15__global__default -> horizon_turbine | 0.15054 | 0.15121 | 1.00439 | -0.00066 | -0.43944 |

## Multi-Weather Agent value

| Weather Strategy | model | D1 MAE | D2 MAE | Overall MAE | ratio_vs_best_single | Improvement vs best single provider (%) |
| --- | --- | --- | --- | --- | --- | --- |
| ECMWF | LightGBM (same settings) | 0.16143 | 0.17609 | 0.16876 | 1.00000 | 0.00000 |
| GFS | LightGBM (same settings) | 0.16757 | 0.18384 | 0.17571 | 1.04117 | -4.11699 |
| ICON | LightGBM (same settings) | 0.18031 | 0.19725 | 0.18878 | 1.11865 | -11.86457 |
| Simple | LightGBM (same settings) | 0.14983 | 0.16308 | 0.15645 | 0.92709 | 7.29092 |
| Weighted | LightGBM (same settings) | 0.15202 | 0.16802 | 0.16002 | 0.94821 | 5.17866 |
| All | LightGBM (same settings) | 0.14887 | 0.16595 | 0.15741 | 0.93276 | 6.72413 |
| All_Disagreement | LightGBM (same settings) | 0.14920 | 0.16647 | 0.15783 | 0.93525 | 6.47498 |
| Full | LightGBM (same settings) | 0.14791 | 0.16516 | 0.15653 | 0.92756 | 7.24375 |

Full is compact Full Agent (24 features), not Full206. Full_No_Performance removes the three explicit wind MAE 30d predictors only. The weighted wind forecast still indirectly uses past performance in BOTH configurations: this comparison measures incremental value of exposing history to ML, not removal of every historical dependency.

Best single provider is chosen by aggregate overall MAE, not a favorable month. D1/D2 provider winners may differ. Individual-provider groups use that provider's temperature; all-provider groups use simple mean temperature. Differences reflect these documented feature strategies, not a clean causal weather-source intervention.
