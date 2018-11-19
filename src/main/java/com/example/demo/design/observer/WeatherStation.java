package com.example.demo.design.observer;

/**
 * 气象站
 *
 * @author dzm
 * @create 2018-11-19 16:57
 **/
public class WeatherStation {
    public static void main(String[] args) {
        WeatherData weatherData = new WeatherData();
        CurrentConditionsDisplay currentConditionsDisplay = new CurrentConditionsDisplay(weatherData);
        StatisticsDisplay statisticsDisplay = new StatisticsDisplay(weatherData);
        weatherData.setMeasurements(0,0,0);
        weatherData.setMeasurements(1,1,1);
    }
}
