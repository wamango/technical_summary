package com.example.demo;

import com.example.demo.design.factory.EncryptFactory;
import com.example.demo.design.strategy.Player;
import com.example.demo.design.template.Bouilli;
import com.example.demo.design.template.DodishTemplate;
import com.example.demo.design.template.EggsWithTomato;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.testng.AbstractTransactionalTestNGSpringContextTests;
import org.testng.annotations.Test;


@SpringBootTest
public class TechnicalSummaryApplicationTests extends AbstractTransactionalTestNGSpringContextTests {
	@Autowired
	private EncryptFactory encryptFactory;

	/**
	 * 策略模式测试
	 */
	@Test
	private void testStrategy() {
		Player player = new Player();
		player.buy(5000D);
		System.out.println("玩家需要付钱：" + player.calLastAmount());
		player.buy(12000D);
		System.out.println("玩家需要付钱：" + player.calLastAmount());
		player.buy(12000D);
		System.out.println("玩家需要付钱：" + player.calLastAmount());
		player.buy(12000D);
		System.out.println("玩家需要付钱：" + player.calLastAmount());
	}

	/**
	 * 工厂模式测试
	 */
	@Test
	private void testFactory()throws Exception{
		int flag = 1;
		System.out.println(encryptFactory.encryptPwdWay(flag,"111111",""));
	}

	/**
	 * 模板模式测试
	 */
	@Test
	private void testTemplate(){
		DodishTemplate dodishTemplate = new EggsWithTomato();
        dodishTemplate.dodish();
        System.out.println("----------");

        dodishTemplate = new Bouilli();
        dodishTemplate.dodish();
	}

}
