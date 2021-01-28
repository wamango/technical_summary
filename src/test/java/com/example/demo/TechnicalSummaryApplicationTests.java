package com.example.demo;

import com.alibaba.fastjson.JSON;
import com.example.demo.ddd.*;
import com.example.demo.design.decorator.*;
import com.example.demo.design.facade.Facade;
import com.example.demo.design.factory.EncryptFactory;
import com.example.demo.design.observer.NewsPaper;
import com.example.demo.design.observer.Reader;
import com.example.demo.design.responsibilitychain.*;
import com.example.demo.design.strategy.Player;
import com.example.demo.design.template.Bouilli;
import com.example.demo.design.template.DodishTemplate;
import com.example.demo.design.template.EggsWithTomato;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.testng.AbstractTransactionalTestNGSpringContextTests;
import org.testng.annotations.Test;


@SpringBootTest
@Slf4j
public class TechnicalSummaryApplicationTests extends AbstractTransactionalTestNGSpringContextTests {
	@Autowired
	private EncryptFactory encryptFactory;

	/**
	 * 策略模式测试
	 */
	@Test(enabled = false)
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
	@Test(enabled = false)
	private void testFactory()throws Exception{
		int flag = 1;
		System.out.println(encryptFactory.encryptPwdWay(flag,"111111",""));
	}

	/**
	 * 模板模式测试
	 */
	@Test(enabled = false)
	private void testTemplate(){
		DodishTemplate dodishTemplate = new EggsWithTomato();
        dodishTemplate.dodish();
        System.out.println("----------");

        dodishTemplate = new Bouilli();
        dodishTemplate.dodish();
	}

	/**
	 *门面模式测试
	 */
	@Test(enabled = false)
	private void testFacade(){
		//可以使用抽象工厂来
		Facade facade = new Facade();
		facade.test();
	}

	/**
	 * 装饰器模式测试，java中io流就用了装饰器模式
	 */
	@Test(enabled = false)
	private void testDecorator(){
//先创建计算基本奖金的类，这也是被装饰的对象
		Component component = new ConcreteComponent();
		//然后对计算的基本奖金进行装饰，这是要组合各个装饰
		//说明，各个装饰者之间最好不要有先后顺序的限制

		//先组合普通业务人员的奖金计算
		Decorator d1 = new MonthPrizeDecorator(component);
		Decorator d2 = new SumPrizeDecorator(d1);

		//用最后组装好的业务对象调用
		double zs = d2.calcPrize("张三",null,null);
		System.out.println("========张三应得奖金："+zs);
		double ls = d2.calcPrize("李四",null,null);
		System.out.println("========李四应得奖金："+ls);

		//如果是业务经理，计算团队奖金
		Decorator d3 = new GroupPrizeDecorator(d2);
		double ww = d3.calcPrize("王五",null,null);
		System.out.println("========王五应得奖金："+ww);
	}

	/**
	 * 观察者模式测试,运用了jdk里面的类
	 */
	@Test(enabled = false)
	private void testObserver(){
		//创建一个目标对象，也就是被观察者
		NewsPaper newsPaper = new NewsPaper();
		//创建阅读者，也就是观察者
		Reader reader1 = new Reader();
		reader1.setName("张一");

		Reader reader2 = new Reader();
		reader2.setName("张二");

		Reader reader3 = new Reader();
		reader3.setName("张三");

		//注册读者
		newsPaper.addObserver(reader1);
		newsPaper.addObserver(reader2);
		newsPaper.addObserver(reader3);
//        newsPaper.deleteObserver(reader2);
		//出版报纸
		newsPaper.setContent("本期内容是观察者模式");
	}

	/**
	 * 责任链测试
	 */
	@Test(enabled = false)
	private void testResponsibilitychain(){
		Handler handler1 = new ConcreteHandler1(null);
		Handler handler2 = new ConcreteHandler2(handler1);
		Handler handler3 = new ConcreteHandler3(handler2);

		Request request1 = new Request(RequestType.TYPE1, "request1");
		handler3.handleRequest(request1);

		Request request2 = new Request(RequestType.TYPE2, "request2");
		handler3.handleRequest(request2);

		Request request3 = new Request(RequestType.TYPE3, "request3");
		handler3.handleRequest(request3);

	}

	@Test
	private void testDtoAssembler(){
		User user = new User("13018065863","test123");
		Basic basic = new Basic("1");
		UserDTO userDTO = DtoAssembler.INSTANCE.toDTO(user,basic);
		log.info("userDTO result:{}", JSON.toJSONString(userDTO));

//		BasicDTO basicDTO = new BasicDTO("1");
//		Basic basic = DtoAssembler.INSTANCE.toEntity(basicDTO);
//		log.info("Basic result:{}", JSON.toJSONString(basic));

	}
}
