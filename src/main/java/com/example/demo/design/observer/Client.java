package com.example.demo.design.observer;


/**
 * 客户端
 *
 * @author dzm
 * @create 2018-11-20 16:21
 **/
public class Client {

    public static void main(String[] args) {
        //创建一个目标对象，也就是被观察者
        NewsPaper subject = new NewsPaper();
        //创建阅读者，也就是观察者
        Reader reader1 = new Reader();
        reader1.setName("张一");

        Reader reader2 = new Reader();
        reader2.setName("张二");

        Reader reader3 = new Reader();
        reader3.setName("张三");

        //注册读者
        subject.attach(reader1);
        subject.attach(reader2);
        subject.attach(reader3);
        subject.detach(reader2);
        //出版报纸
        subject.setContent("本期内容是观察者模式");
    }
}
