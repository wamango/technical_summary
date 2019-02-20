package com.example.demo.design.factory.simpleFactory;

/**
 * 工厂类，用来创建API对象
 *
 * @author dzm
 * @create 2019-02-13 16:46
 **/
public class Facory {

    /**
     *具体创建Api对象方法
     * @param condition
     * @return
     */
    public static Api createApi(int condition){
        Api api = null;
        if(condition==1){
            api = new ImplA();
        }else if(condition==2){
            api = new ImplB();
        }
        return api;
    }
}
