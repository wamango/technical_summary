package com.example.demo.design.observer;

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
     * 更新方法
     *
     * @param subject 传入目标对象，方便获取相应的目标对象的状态
     */
    @Override
    public void update(Subject subject) {
        System.out.println(name+"收到报纸了，阅读它，内容是："+((NewsPaper)subject).getContent());
    }
}
