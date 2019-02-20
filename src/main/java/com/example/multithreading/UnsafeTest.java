package com.example.multithreading;

import sun.misc.Unsafe;

import java.lang.reflect.Field;

/**
 * unsafe类测试
 *
 * @author dzm
 * @create 2019-01-29 15:06
 **/
public class UnsafeTest {
    //获取unsafe示例
    static final Unsafe unsafe;

    //记录变量state在类UnsafeTest中的偏移量
    static final long stateOffset;

    //变量
    private volatile long state = 0;

    static {
        try {
            //使用反射获取Unsafe的成员变量UnsafeTest
            Field field = Unsafe.class.getDeclaredField("theUnsafe");

            //设置为可存取
            field.setAccessible(true);

            //获取该变量的值
            unsafe = (Unsafe)field.get(null);

            //获取state变量在类UnsafeTest中的偏移值
            stateOffset = unsafe.objectFieldOffset(UnsafeTest.class.getDeclaredField("state"));
        } catch (Exception e) {
            System.out.println(e.getLocalizedMessage());
            throw new Error(e);
        }
    }

    public static void main(String[] args) {
        //创建实例
        UnsafeTest test = new UnsafeTest();
        /**
         * boolean compareAndSwapInt(Object obj,long offset,long expect,long update)
         * 比较对象obj中偏移量为offset的变量的值是否与expect相等，相等则使用update值更新，然后返回true，否则返回false
         */
        Boolean sucess = unsafe.compareAndSwapInt(test,stateOffset,0,1);
        System.out.println(sucess);
    }
}
