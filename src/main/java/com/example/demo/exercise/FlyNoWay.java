package com.example.demo.exercise;

/**
 * 不会飞
 *
 * @author dzm
 * @create 2018-08-22 18:19
 **/
public class FlyNoWay implements FlyBehavior {
    @Override
    public void fly() {
        System.out.println("I can't fly");
    }
}
