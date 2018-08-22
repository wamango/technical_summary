package com.example.demo.design.facade;

/**
 * 模板A的实现类
 *
 * @author dzm
 * @create 2018-08-22 14:18
 **/
public class AModuleApiImpl implements AModuleApi {
    /**
     * 提供给外部系统
     */
    @Override
    public void a1() {
        System.out.println("模板A的a1方法");
    }

    @Override
    public void a2() {
        System.out.println("模块A的a2方法");
    }

    @Override
    public void a3() {
        System.out.println("模块A的a3方法");
    }
}
