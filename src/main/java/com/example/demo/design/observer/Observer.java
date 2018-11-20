package com.example.demo.design.observer;

/**
 * 观察者接口，定义一个更新的方法给那些发生改变时的被通知的对象
 */
public interface Observer {

    /**
     * 被通知的方法
     * @param subject 传入目标对象，可以获取报纸的内容
     */
    public void update(Subject subject);
}
