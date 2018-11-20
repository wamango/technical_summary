package com.example.demo.design.observer;

import java.util.Observable;
import java.util.Observer;

/**
 * 具体的观察者实现
 *
 * @author dzm
 * @create 2018-11-20 16:11
 **/
public class Reader implements Observer {

    /**
     * 读者的姓名
     */
    private String name;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }


    /**
     * This method is called whenever the observed object is changed. An
     * application calls an <tt>Observable</tt> object's
     * <code>notifyObservers</code> method to have all the object's
     * observers notified of the change.
     *
     * @param o   the observable object.
     * @param content an argument passed to the <code>notifyObservers</code>
     */
    @Override
    public void update(Observable o, Object content) {
        System.out.println(name+"收到报纸了，阅读它，推送模式，内容是："+content);
        System.out.println(name+"收到报纸了，阅读它，拉取模式，内容是："+((NewsPaper)o).getContent());
    }
}
