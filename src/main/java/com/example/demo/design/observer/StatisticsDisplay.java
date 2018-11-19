package com.example.demo.design.observer;

/**
 * 统计显示
 *
 * @author dzm
 * @create 2018-11-19 16:53
 **/
public class StatisticsDisplay implements Observer {
    public StatisticsDisplay(Subject weatherData){
        weatherData.resisterObserver(this);
    }

    /**
     * 更新
     *
     * @param temp     温度
     * @param humidity 湿度
     * @param pressure 气压
     */
    @Override
    public void update(float temp, float humidity, float pressure) {
        System.out.println("StatisticsDisplay.update:"+temp+" "+humidity+" "+pressure);
    }
}
