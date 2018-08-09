package com.example.demo.design.strategy;

/**
 * 普通玩家
 *
 * @author dzm
 * @create 2018-08-09 23:35
 **/
@PriceRegion(max = 10000)
public class Orgnic implements CalPrice{

    /**
     * 原价
     * @param orgnicPrice
     * @return
     */
    @Override
    public Double calPrice(Double orgnicPrice) {
        return orgnicPrice;
    }
}
