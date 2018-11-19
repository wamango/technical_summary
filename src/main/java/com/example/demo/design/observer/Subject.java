package com.example.demo.design.observer;

/**
 * 主题
 *
 * @author dzm
 * @create 2018-11-19 16:31
 **/
public interface Subject {
    void resisterObserver(Observer o);

    void removeObserver(Observer o);

    void notifyObserver();
}
