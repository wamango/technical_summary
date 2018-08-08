package com.example.demo.design.template;

/**
 * 西红柿炒鸡蛋类，继承模板，重写模板中的抽象方法
 */
public class EggsWithTomato extends DodishTemplate {
    @Override
    public void preparation() {
        System.out.println("洗切西红柿，打鸡蛋");
    }

    @Override
    public void doing() {
        System.out.println("把西红柿和鸡蛋倒入锅里炒");
    }

    @Override
    public void carriedDishes() {
        System.out.println("将炒好的西红柿和鸡蛋装盘");
    }
}
