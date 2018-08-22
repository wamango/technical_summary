package com.example.demo.design.facade;

/**
 * 外观（门面）模式类
 *
 * @author dzm
 * @create 2018-08-21 17:56
 **/
public class Facade implements FacadeApi {

    private AModuleApiImpl aModuleApi;
    private BModuleApiImpl bModuleApi;
    public Facade(){
        aModuleApi = new AModuleApiImpl();
        bModuleApi = new BModuleApiImpl();
    }


    /**
     * a1,b1,c1三个对外提供的接口
     */
    @Override
    public void a1() {
        aModuleApi.a1();
    }

    @Override
    public void b1() {
        bModuleApi.b1();
    }


    /**
     * 提供对的组合方法
     */
    @Override
    public void test() {
        a1();
        b1();
    }
}
