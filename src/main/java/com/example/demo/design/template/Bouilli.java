package com.example.demo.design.template;

/**
 * 红烧肉类，继承模板，重写模板中的抽象方法
 */
public class Bouilli extends DodishTemplate {
    @Override
    public void preparation() {
        System.out.println("切肉");
    }

    @Override
    public void doing() {
        System.out.println("倒入锅中煮");
    }

    @Override
    public void carriedDishes() {
        System.out.println("起锅，装盘");
    }
}
