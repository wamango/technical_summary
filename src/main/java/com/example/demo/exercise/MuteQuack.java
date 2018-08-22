package com.example.demo.exercise;

/**
 * 不会呱呱叫
 *
 * @author dzm
 * @create 2018-08-22 18:24
 **/
public class MuteQuack implements QuackBehavior {
    @Override
    public void quack() {
        System.out.println("MuteQuack");
    }
}
