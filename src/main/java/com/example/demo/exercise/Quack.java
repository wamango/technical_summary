package com.example.demo.exercise;

/**
 * 呱呱叫
 *
 * @author dzm
 * @create 2018-08-22 18:22
 **/
public class Quack implements QuackBehavior {
    @Override
    public void quack() {
        System.out.println("Quack");
    }
}
