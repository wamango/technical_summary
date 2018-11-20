package com.example.demo.design.observer;

import java.util.Observable;

/**
 * 具体的目标实现
 *
 * @author dzm
 * @create 2018-11-20 16:06
 **/
public class NewsPaper extends Observable {

    public NewsPaper(){
        super();
    }

    /**
     * 报纸的具体内容
     */
    private String content;

    /**
     * 获取报纸上的具体内容
     * @return 报纸上的具体内容
     */
    public String getContent() {
        return content;
    }

    /**
     * 示意，设置报纸的具体内容，相当于出版报纸
     * @param content 报纸的具体内容
     */
    public void setContent(String content) {
        this.content = content;
        this.setChanged();
        //内容有了，说明要出版报纸了，通知所有的读者
        this.notifyObservers(content);

    }
}
