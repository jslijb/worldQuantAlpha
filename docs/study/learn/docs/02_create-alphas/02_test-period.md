# Test Period

> **归档信息**
> - 页面：<https://platform.worldquantbrain.com/learn/documentation/test-period>
> - 页面 id：`test-period` ｜ 课程：`Creating Alphas` ｜ 预计时长：PT3M
> - 平台最后更新：2026-08-26T01:56:22.574685-04:00
> - 来源：**平台官方 tutorial-pages 接口原文**（`GET /tutorial-pages/{id}`），文字/表格/图片均为原样转换，未改写
> - 抓取：`src/tools/fetch_learn_docs.py`｜抓取日期 2026-09-15

---


![Settings dropdown](../images/test-period/01_Settings_dropdown.png)

The Test Period is a feature designed to enhance your Alpha and SuperAlpha testing process. This tool allows you to set a separate test period from your IS period, providing a more flexible approach to testing your research ideas.

Using the Feature:

The Test Period feature is designed to help you avoid overfitting. It allows you to divide your In-Sample (IS) period into a Train and Test period. The Train period can be utilized to develop your Alphas and SuperAlphas, while the Test period is ideal for validating them. An Alpha or SuperAlpha that is developed based on the simulation results of Training Period and performs well in both periods is likely a strong candidate for submission and may have avoided overfitting.

While choosing a Test period does not directly affect the simulation, it influences the statistics and the visualization. The submission tests will run on the entire 5-year period, with the simulation running on the entire 5-year IS. However, if a testing period is chosen, the simulation stats will be divided into two sections: one covering the training period and another for the test period.

Navigating the Feature:

- Selecting the Test Period: In Simulation Settings, you can define a test period corresponding to the final 0-5 years of the IS period. By default, no test period is set (0 years).
- Visualizing the Test Period: The Stats Summary defaults to the training period. You can view the stats for the test period by clicking on the “Show test period” button.
- Identifying the Test Period on Graphs: The lines representing the test period on the graphs are colored orange.
- Choosing the Stats Summary: You can select between the Stats Summary for the test period or the entire IS period by choosing the “TEST” or “IS” in the Summary section, respectively.
- Hiding the Test Period: A button “Hide test period” allows you to hide the test period, if desired. Note that an Alpha or SuperAlpha can only be submitted when the Test Period is revealed by clicking on the “Show test period” button.
- Understanding the Stats: The yearly IS stats are divided between Train and Test periods, represented by blue and orange indicators respectively.


![Test Period Graph and Table.png](../images/test-period/02_Test_Period_Graph_and_Table.png)

A. Orange - test period PnL, Blue - Train period PnL. B. View IS summary by selecting different periods
