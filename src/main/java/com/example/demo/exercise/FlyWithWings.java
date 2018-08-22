package com.example.demo.exercise;

/**
 * 有翅膀的飞行
 *
 * @author dzm
 * @create 2018-08-22 18:18
 **/
public class FlyWithWings implements FlyBehavior{
    @Override
    public void fly() {
        System.out.println("I'm flying");
    }
}
