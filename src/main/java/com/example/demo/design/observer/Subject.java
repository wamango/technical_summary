package com.example.demo.design.observer;

import java.util.ArrayList;
import java.util.List;

/**
 * 观察者
 *
 * @author dzm
 * @create 2018-11-20 15:51
 **/
public class Subject {
    /**
     * 用来保存注册的观察者对象，也就是读者
     */
    private List<Observer> readers;

    public Subject(){
        readers = new ArrayList<>();
    }

    /**
     * 注册观察者，读者
     * @param observer 观察者对象
     */
    public void attach(Observer observer){
        readers.add(observer);
    }

    /**
     * 删除观察者，读者取消订阅
     * @param observer 观察者
     */
    public void detach(Observer observer){
        readers.remove(observer);
    }

    /**
     * 通知所有注册的观察者对象，读者
     */
    public void notifyObserver(){
        for (Observer reader : readers){
            reader.update(this);
        }
    }


}
