package com.example.demo.exercise;

/**
 * 测试类
 *
 * @author dzm
 * @create 2018-08-22 18:25
 **/
public class MiniDuckSimulator {

    public static void main(String[] args) {
        Duck mallard = new MallardDuck();
        mallard.setFlyBehavior(new FlyNoWay());
        mallard.performFly();
        mallard.setQuackBehavior(new MuteQuack());
        mallard.performQuack();
    }
}
