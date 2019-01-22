package com.example.multithreading;

import java.util.concurrent.*;

/**
 * 线程创建方式
 *
 * @author dzm
 * @create 2019-01-22 11:50
 **/
public class ThreadTest {

    static  ExecutorService es = Executors.newFixedThreadPool(10);

    public static class MyThread extends Thread{

        /**
         * If this thread was constructed using a separate
         * <code>Runnable</code> run object, then that
         * <code>Runnable</code> object's <code>run</code> method is called;
         * otherwise, this method does nothing and returns.
         * <p>
         * Subclasses of <code>Thread</code> should override this method.
         *
         * @see #start()
         * @see #stop()
         */
        @Override
        public void run() {
            System.out.println("I am a child thread -- thread");
        }
    }

    public static void main(String[] args) {
        //创建线程
        MyThread myThread = new MyThread();
        //启动线程
        myThread.start();

        RunableTask runableTask = new RunableTask();
        new Thread(runableTask).start();
        new Thread(runableTask).start();

        //创建异步线程
        FutureTask<String> futureTask = new FutureTask<String>(new CallerTask());
        //启动线程
        new Thread(futureTask).start();
        try{
            //等待任务执行完毕，并返回结果
            String result = futureTask.get();
            System.out.println(result);
        }catch (Exception e){
            e.printStackTrace();
        }
    }


    public static class RunableTask implements Runnable{

        /**
         * When an object implementing interface <code>Runnable</code> is used
         * to create a thread, starting the thread causes the object's
         * <code>run</code> method to be called in that separately executing
         * thread.
         * <p>
         * The general contract of the method <code>run</code> is that it may
         * take any action whatsoever.
         *
         * @see Thread#run()
         */
        @Override
        public void run() {
            System.out.println("I am a child thread -- runable");
        }
    }

    public static class CallerTask implements Callable<String>{

        /**
         * Computes a result, or throws an exception if unable to do so.
         *
         * @return computed result
         * @throws Exception if unable to compute a result
         */
        @Override
        public String call() throws Exception {
            return "HELLO";
        }
    }

}
