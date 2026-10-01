# 税金ナビゲーター 税制データ（tax-parameters-v1.json）

税金ナビゲーターのアプリは、このファイルを1日2回ほど読み込みます。
毎年変わる税率や上限額は、ここを書き換えて公開するだけで、アプリをアップデートしなくても反映されます。

- 公開 URL：`https://nao22c.github.io/TaxNavi/data/tax-parameters-v1.json`
- 反映の目安：GitHub Pages のキャッシュで最大10分ほどかかり、アプリ側は前回の確認から12時間以上たったときにだけ読みに行きます。設定画面の「今すぐ確認」を押せばすぐ確認できます。
- 個人の情報は送られてきません。アプリはこのファイルを読むだけです。

## 更新の手順

1. `tax-parameters-v1.json` の値を書き換える。
2. `dataVersion` を今日の日付（`yyyy-MM-dd`）にする。**今の値より新しい日付にしないと、アプリは取り込みません。**
3. 検証スクリプトを実行し、`OK` と表示されることを確認する。
   ```
   python3 TaxNavi/data/validate.py
   ```
4. コミットして push する。

アプリは、取り込む前に同じチェックをします。範囲外の値や形の崩れがあれば、そのファイルは使わずに前のデータのまま動きます。

## 毎年の更新でよく触る場所

| 時期 | 内容 | 場所 |
|---|---|---|
| 3月 | 協会けんぽの健康保険料率（47都道府県と全国平均）、介護保険料率 | `socialInsurance.prefectureHealthRates`、`nationalHealthRate`、`careRate` |
| 4月 | 子ども・子育て支援金率、雇用保険料率（労働者負担）、国民年金保険料 | `socialInsurance.childSupportRate`、`employmentInsuranceWorkerRate`、`nationalPensionMonthly` |
| 8月 | 失業給付（基本手当）の賃金日額の下限・上限、給付率の境目、日額の上限 | `employmentInsurance.unemployment` |
| 8月 | 育休給付の賃金月額の上限・下限 | `employmentInsurance.leave.childcareWageMonthlyCap`、`childcareWageMonthlyFloor` |
| 12月〜翌年 | 税制改正（基礎控除、給与所得控除、扶養の所得要件など） | `incomeYears` に新しい年を追加し、`currentIncomeYear` を切り替える |

- 料率は「労使合計」の率を小数で書きます（例：9.90% → `0.099`）。ただし `employmentInsuranceWorkerRate` だけは労働者負担分です。
- 失業給付の上限は年齢区分ごとに4つ並べます：30歳未満、30〜44歳、45〜59歳、60〜64歳。
- 表の最後の区切りは `"upperBound": null`（上限なし）にします。
- 年の切り替え（例：令和9年分）は、計算の仕組みが同じなら JSON だけで対応できます。新しい控除の追加など、仕組みが変わる改正はアプリのアップデートが必要です。

## ファイル形式を変えるとき

項目の追加や構造の変更が必要になったら、このファイルは変えずに `tax-parameters-v2.json` を新しく作り、新しいアプリにそちらを読ませます。古いアプリは v1 を読み続けるので、v1 もしばらく更新を続けてください。
