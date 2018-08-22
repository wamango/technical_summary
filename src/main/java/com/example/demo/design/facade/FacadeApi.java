package com.example.demo.design.facade;

/**
 * 门面类
 *
 * @author dzm
 * @create 2018-08-22 10:41
 **/
public interface FacadeApi {
    /**
     * a1,b1,c1三个对外提供的接口
     */
    public void a1();
    public void b1();

    /**
     * 提供对的组合方法
     */
    public void test();
}
