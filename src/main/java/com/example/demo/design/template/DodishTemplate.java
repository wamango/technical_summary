package com.example.demo.design.template;

/**
 * 模板类
 */
public abstract class DodishTemplate {

    /**
     * 做菜的整个过程（公用的可以写在里面）
     */
    public void dodish(){
        start();
        preparation();
        doing();
        carriedDishes();
        end();
    }

    private void start(){
        System.out.println("开始做菜");
    }

    private void end(){
        System.out.println("结束做菜");
    }

    /**
     * 备料
     */
    public abstract void preparation();

    /**
     *做菜
     */
    public abstract void doing();

    /**
     * 上菜
     */
    public abstract void carriedDishes();
}
