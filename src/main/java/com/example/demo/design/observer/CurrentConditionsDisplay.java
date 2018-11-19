package com.example.demo.design.observer;

/**
 * 当前条件显示
 *
 * @author dzm
 * @create 2018-11-19 16:56
 **/
public class CurrentConditionsDisplay implements Observer {
    public CurrentConditionsDisplay(Subject weatherData){
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
        System.out.println("CurrentConditionsDisplay.update: " + temp + " " + humidity + " " + pressure);
    }
}
