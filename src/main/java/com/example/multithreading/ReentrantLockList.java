package com.example.multithreading;

import com.google.common.util.concurrent.ThreadFactoryBuilder;

import java.util.ArrayList;
import java.util.concurrent.Executor;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;

/**
 * 重入锁
 *
 * @author dzm
 * @create 2019-02-22 15:13
 **/
public class ReentrantLockList {
    //线程不安全的list
    private ArrayList<String> array = new ArrayList<String>();
    //独占锁
    private volatile ReentrantLock lock = new ReentrantLock(true);
    //添加元素
    public void add(String e){
        lock.lock();
        try{
            array.add(e);
        }finally {
            lock.unlock();
        }
    }
    //删除元素
    public void remove(String e){
        lock.lock();
        try {
            array.remove(e);
        }finally {
            lock.unlock();
        }
    }
    //获取数据
    public String get(int index){
        lock.lock();
        try{
            return array.get(index);
        }finally {
            lock.unlock();
        }
    }

//    public static void main(String[] args) {
//        ReentrantLockList reentrantLockList = new ReentrantLockList();
//        Executor es = new ThreadPoolExecutor(3, 3,
//                0L, TimeUnit.MILLISECONDS,
//                new LinkedBlockingQueue<Runnable>(),new ThreadFactoryBuilder().setNameFormat("thread-call-runner-%d").build());
//        for(int i=0;i<3;i++){
//            es.execute(new Runnable() {
//                @Override
//                public void run() {
//                    reentrantLockList.add(Thread.currentThread()+"1");
//                    System.out.println(Thread.currentThread()+"正在执行");
//                }
//            });
//        }
//        reentrantLockList.array.stream().forEach(string->{
//            System.out.println(string);
//        });
//    }

}
