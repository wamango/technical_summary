package com.example.demo.design.observer;

import java.util.ArrayList;
import java.util.List;

/**
 * 天气数据
 *
 * @author dzm
 * @create 2018-11-19 16:35
 **/
public class WeatherData implements Subject {
    private List<Observer> observers;
    private float temperature;
    private float humidity;
    private float pressure;

    public WeatherData(){
        observers = new ArrayList<>();
    }

    /**
     * 测量
     * @param temperature
     * @param humidity
     * @param pressure
     */
    public void setMeasurements(float temperature, float humidity, float pressure) {
        this.temperature = temperature;
        this.humidity = humidity;
        this.pressure = pressure;
        notifyObserver();
    }

    /**
     * 注册观察者
     * @param o
     */
    @Override
    public void resisterObserver(Observer o) {
        observers.add(o);
    }

    /**
     * 删除观察者
     * @param o
     */
    @Override
    public void removeObserver(Observer o) {
        int i = observers.indexOf(o);
        if(i>=0){
            observers.remove(i);
        }
    }

    /**
     * 通知观察者
     */
    @Override
    public void notifyObserver() {
        for(Observer observer :observers){
            observer.update(temperature,humidity,pressure);
        }
    }
}
