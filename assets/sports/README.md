# Sport image provenance

The icons in this directory are **real third-party image files**, stored in this repository and rendered via `<img>`, not assistant-drawn SVGs.

| File | Upstream source | Licence / status |
|---|---|---|
| football.svg | [Premier League brand logo in theSVG](https://github.com/glincker/thesvg/blob/main/public/icons/premier-league/default.svg) | Official Premier League trademark; only used for Premier League fixtures |\n| football-generic.svg | [Font Awesome Free futbol](https://github.com/FortAwesome/Font-Awesome/blob/7.x/svgs/solid/futbol.svg) | CC BY 4.0; non-Premier League football |
| rugby.svg | [Material Design Icons rugby](https://github.com/Templarian/MaterialDesign/blob/master/svg/rugby.svg) | Apache 2.0 |
| gaelic-football.svg | [Material Design Icons soccer](https://github.com/Templarian/MaterialDesign/blob/master/svg/soccer.svg) | Apache 2.0; **generic ball, not official GAA logo** |
| nfl.svg | [NFL brand shield in theSVG](https://github.com/glincker/thesvg/blob/main/public/icons/nfl/default.svg) | Official NFL trademark; brand asset from third-party archive |
| f1.svg | [F1 2026 assets F1 logo](https://github.com/mark-boots/f1-2026-assets/blob/main/assets/f1logo.svg) | Official F1 branding redistributed by an unofficial repository; trademark owned by Formula One; use for identification only |
| snooker.svg | [Material Design Icons billiards](https://github.com/Templarian/MaterialDesign/blob/master/svg/billiards.svg) | Apache 2.0; generic billiards symbol |
| darts.svg | [Font Awesome Free bullseye](https://github.com/FortAwesome/Font-Awesome/blob/7.x/svgs/solid/bullseye.svg) | CC BY 4.0; generic target |
| golf.svg | [Font Awesome Free golf ball tee](https://github.com/FortAwesome/Font-Awesome/blob/7.x/svgs/solid/golf-ball-tee.svg) | CC BY 4.0 |
| hurling.svg | [Material Design Icons hockey-sticks](https://github.com/Templarian/MaterialDesign/blob/master/svg/hockey-sticks.svg) | Apache 2.0; **placeholder, not an official hurley graphic** |
| racing.svg | [Font Awesome Free horse](https://github.com/FortAwesome/Font-Awesome/blob/7.x/svgs/solid/horse.svg) | CC BY 4.0 |

**Important:** F1, NFL and Premier League have genuine branded marks sourced from third-party repositories; the remaining assets are third-party sport pictograms, not official league or governing-body logos. The GAA and hurling icons need better licensed, sport-specific assets before they can be considered accurate representations of the reference screenshot. The use of trademarks does not imply endorsement.

## Official brand asset rollout (November 2026)

The assets below were **downloaded and committed** by `sync_brand_assets.py` / `.github/workflows/sync-brand-assets.yml` from the published Wikimedia Commons originals. See `official-sources.json` for the exact Commons pages. These are original third-party image files, not redrawn logos.

| Local asset | Brand depicted | When used |
|---|---|---|
| `gaa-official.jpg` | Gaelic Athletic Association GAA wordmark | Gaelic football and hurling/camogie fixtures |
| `irfu-official.svg` | Irish Rugby Football Union text logo | Ireland rugby fixtures |
| `rugby-world-cup.svg` | Rugby World Cup branding | Rugby World Cup fixtures |
| `snooker-federation.svg` | World Snooker Federation | Snooker category (representative governing-body logo, **not** WST tour branding) |
| `pdc-official.png` | Professional Darts Corporation | General PDC darts category (archival logo; may not be current) |
| `darts-world-series.svg` | PDC World Series of Darts | World Series of Darts fixtures |
| `racing-jockey-club.png` | The Jockey Club (UK) | British racing fixtures at matched racecourses |
| `pga-tour-official.svg` | PGA Tour | PGA Tour / FedExCup fixtures; sourced from [esnWorld](https://github.com/easonwc/esnWorld/blob/main/public/logos/golf-tours/pga.svg) |
| `lpga-tour-official.svg` | LPGA Tour | LPGA fixtures; sourced from [esnWorld](https://github.com/easonwc/esnWorld/blob/main/public/logos/golf-tours/lpga.svg) |

**Accuracy rule:** Never display an unrelated competition's logo as if it were the event's own. When a matching brand is unavailable (for example DP World Tour golf, other national rugby teams or Irish horse racing), show the locally stored generic sport pictogram rather than a false official badge. `*-generic.svg` assets provide those fallbacks. A brand logo is not an endorsement, and copyright/trademark permissions remain with the respective rights holders.

The live page references only files committed in `assets/sports/`, and uses a local fallback if an asset cannot load.
