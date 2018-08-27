package com.example.demo.exercise;

/**
 * 绿头鸭
 *
 * @author dzm
 * @create 2018-08-22 18:31
 **/
public class MallardDuck extends Duck{

    @Override
    public void display() {
        System.out.println("I'm a real Mallard duck");
    }

    public MallardDuck(){
        quackBehavior = new MuteQuack();
        flyBehavior = new FlyNoWay();
    }
}
