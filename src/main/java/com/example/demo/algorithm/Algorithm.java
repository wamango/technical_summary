package com.example.demo.algorithm;

import java.util.*;

/**
 * 常规算法类
 *
 * @author dzm
 * @create 2018-02-26 18:16
 **/
public class Algorithm {
    /**
     * 两个整数a,b，不使用+号的情况下，计算这两个数字的和
     */
    private static int aplusb(int a, int b) {
        if (a == 0) {
            return b;
        }
        if (b == 0) {
            return a;
        }
        int c, d;
        //对两个整数进行异或操作,然后做与操作，左移一位,递归直到没有进位为止
        c = a ^ b;
        d = (a & b) << 1;
        return aplusb(c, d);
    }

    /**
     * 设计一个算法，计算出n阶乘中尾部零的个数
     * 11! = 39916800，因此应该返回 2
     */
    private static long trailingZeros(long n) {
        //1.直接计算结果,然后转为字符串进行判断,结果是否为零的情况,在n值较大的时候,性能太差
        long sum = 1;
        for (int i = 1; i <= n; i++) {
            sum *= i;
        }
        String sumStr = String.valueOf(sum);
        int count = 1;
        int index = sumStr.indexOf("0");
        for (int i = index + 1; i < sumStr.length(); i++) {
            if (i + 1 <= sumStr.length()) {
                if (!sumStr.substring(i, i + 1).equals("0")) {
                    count = 0;
                }
                count++;
            }
        }
        return count;

        //2. 加法操作，从5开始，每次进5，然后判断，但是效果达不到O(logN)
//        long count = 0;
//        long pwr = 25;
//        for (long temp = 5; temp <= n; temp += 5) {
//            //for循环内部的temp都是5的倍数，因此首先+1操作
//            count++;
//            pwr = 25;
//            // 判断是不是25、125、625...的倍数，并根据每次pwr的变化进行+1操作
//            while (temp % pwr == 0) {
//                count++;
//                pwr *= 5;
//            }
//        }
//        return count;
//        //3.每次除5 http://blog.csdn.net/surp2011/article/details/51168272
//        long count = 0;
//        long temp = n / 5;
//        while (temp != 0) {
//            count += temp;
//            temp /= 5;
//        }
//        return count;
    }

    /**
     * 计算两个数组的交集,交集里面的数字可重复的
     *
     * @param nums1
     * @param nums2
     */
    public static int[] intersection(int[] nums1, int[] nums2) {
        //先对两个数组进行排序，然后用两个指针进行比较
        List<Integer> list = new ArrayList<Integer>();
        Arrays.sort(nums1);
        Arrays.sort(nums2);
        int i = 0;
        int j = 0;
        while (i < nums1.length && j < nums2.length) {
            if (nums1[i] == nums2[j]) {
                list.add(nums1[i]);
                ++i;
                ++j;
            } else if (nums1[i] > nums2[j]) {
                ++j;
            } else {
                ++i;
            }
        }
        int[] result = new int[list.size()];
        for (int k = 0; k < list.size(); k++) {
            result[k] = list.get(k);
        }//如果交集里面的元素去重，那么可以用hashset等方法
        return result;
    }


    /**
     * //如果交集里面的元素去重，那么可以用hashset等方法
     *
     * @param nums1
     * @param nums2
     */
    public static int[] intersectionOnly(int[] nums1, int[] nums2) {
//        //先对两个数组进行排序，然后用两个指针进行比较,把结果放入hashset里面去掉重复元素
        Set<Integer> set = new HashSet<>();
        Arrays.sort(nums1);
        Arrays.sort(nums2);
        int i = 0;
        int j = 0;
        while (i < nums1.length && j < nums2.length) {
            if (nums1[i] == nums2[j]) {
                set.add(nums1[i]);
                ++i;
                ++j;
            } else if (nums1[i] > nums2[j]) {
                ++j;
            } else {
                ++i;
            }
        }
        int[] result = new int[set.size()];
        Iterator<Integer> it = set.iterator();
        int count = 0;
        while (it.hasNext()) {
            result[count] = it.next();
            ++count;
        }
        return result;

        //先把一个数组放入hashMap，然后再放入另外一个数组
//        Map<Integer, Integer> map = new HashMap<>();
//        for (int i = 0; i < nums1.length; i++) {
//            map.put(nums1[i], i);
//        }
//        Map<Integer, Integer> resMap = new HashMap<>();
//        for (int j = 0; j < nums2.length; j++) {
//            if (map.containsKey(nums2[j])) {
//                resMap.put(nums2[j], j);
//            }
//        }
//        int[] result = new int[resMap.size()];
//        int count = 0;
//        for (Integer it : resMap.keySet()) {
//            result[count] = it;
//            ++count;
//        }
//        return result;
    }

    /**
     * 实现一个leftpad库(左填充)
     *
     * @param originalStr
     * @param size
     * @return
     */
    public static String leftPad(String originalStr, int size) {
        // Write your code here
        //先判断字符串的长度，然后从下标0开始插入空格
        StringBuffer sb = new StringBuffer();
        if (size > originalStr.length()) {
            //判断这个数字大于字符串的长度，否则不需要左填充
            sb.append(originalStr);
            for (int i = 0; i < size - originalStr.length(); i++) {
                sb.insert(0, " ");
            }
            return sb.toString();
        }
        return originalStr;
    }

    /**
     * 实现一个leftpad库(左填充，替换)
     *
     * @param originalStr
     * @param size
     * @return
     */
    static public String leftPad(String originalStr, int size, char padChar) {
        // write your code here
        //先判断字符串的长度，然后从下标0开始插入空格
        StringBuffer sb = new StringBuffer();
        if (size > originalStr.length()) {
            //判断这个数字大于字符串的长度，否则不需要左填充
            sb.append(originalStr);
            for (int i = 0; i < size - originalStr.length(); i++) {
                sb.insert(0, padChar);
            }
            return sb.toString();
        }
        return originalStr;
    }

    /**
     * 检查两棵二叉树是否等价。
     * 等价的意思是说，首先两棵二叉树必须拥有相同的结构，并且每个对应位置上的节点上的数都相等。
     *
     * @param a
     */
    public static boolean isIdentical(TreeNode a, TreeNode b) {
        // write your code here
        if (a == null && b == null) {
            return true;
        } else if (a == null || b == null) {
            return false;
        } else if (a.val != b.val) {
            return false;
        } else if (a.val == b.val) {
            return (isIdentical(a.left, b.left) && isIdentical(a.right, b.right));
        }
        return false;
    }

    /**
     * 给定一个字符串所表示的括号序列，包含以下字符： '(', ')', '{', '}', '[' and ']'， 判定是否是有效的括号序列。
     * 括号必须依照 "()" 顺序表示， "()[]{}" 是有效的括号，但 "([)]"则是无效的括号。
     * E push(E item)
     * 把项压入堆栈顶部。
     * E pop()
     * 移除堆栈顶部的对象，并作为此函数的值返回该对象。
     * E peek()
     * 查看堆栈顶部的对象，但不从堆栈中移除它。
     * boolean empty()
     * 测试堆栈是否为空。
     *
     * @param s
     */
    public static boolean isValidParentheses(String s) {
        //先判断字符串是否为空，是否是2的倍数，否则就肯定是无效的括号
        if (s == null || s.length() == 0 || s.length() % 2 != 0) {
            return false;
        }
        Stack<Character> stack = new Stack<>();
        //定义一个标识
        boolean flag = true;
        for (int i = 0; i < s.length(); i++) {
            if (s.charAt(i) == '(' || s.charAt(i) == '[' || s.charAt(i) == '{') {
                stack.push(s.charAt(i));
            } else if (s.charAt(i) == ')') {
                if (!stack.empty() && stack.peek() == '(') {
                    stack.pop();
                } else {
                    flag = false;
                    break;
                }
            } else if (s.charAt(i) == ']') {
                if (!stack.empty() && stack.peek() == '[') {
                    stack.pop();
                } else {
                    flag = false;
                    break;
                }
            } else if (s.charAt(i) == '}') {
                if (!stack.empty() && stack.peek() == '{') {
                    stack.pop();
                } else {
                    flag = false;
                    break;
                }
            }
        }
        if (!stack.empty()) {
            flag = false;
        }
        return flag;
    }

    /**
     * 有一个n层的建筑。如果一个鸡蛋从第k层及以上落下，它会碎掉。如果从低于这一层的任意层落下，都不会碎。
     * 现在有两个鸡蛋,找出最少次数（动态规划）
     *
     * @param n
     */
    public static int dropEggs(int n) {
        int eggs = 2;
        int[][] state = new int[3][n + 1];
        //第二步永远是考虑边界，也就是初始化动态规划的备忘录
        //先考虑eggs的边界
        for (int i = 0; i <= n; i++) {
            //首先是eggs=0的情况
            state[0][i] = 0;
            //然后是eggs=1的情况
            //eggs=1的时候，肯定是从第0层一直往上实验
            state[1][i] = i;
        }
        //再考虑floors的边界
        for (int i = 1; i <= 2; i++) {
            //首先是floors=0的情况
            state[i][0] = 0;
            //然后是floors=1的情况
            state[i][1] = 1;
        }
        for (int floor = 2; floor <= n; floor++) {
            int result = Integer.MAX_VALUE;
            for (int drop = 1; drop <= floor; drop++) {
                int broken = state[1][drop - 1];
                int unbroken = state[2][floor - drop];
                int condition = Math.max(broken, unbroken) + 1;
                result = Math.min(condition, result);
            }
            state[2][floor] = result;
        }
        return state[2][n];
    }

    public static int dropEggs2(int eggs, int floors) {
        // write your code here
        //第一步永远是创建动态规划的备忘录,也叫状态转移矩阵
        //记住：二维数组里的length是0-start的，又因为包含层数为0或鸡蛋为0的情况，所以定义行高和列宽的时候自然要加1
        int[][] state = new int[eggs + 1][floors + 1];

        //第二步永远是考虑边界，也就是初始化动态规划的备忘录
        //先考虑eggs的边界
        for (int i = 0; i <= floors; i++) {
            //首先是eggs=0的情况
            state[0][i] = 0;
            //然后是eggs=1的情况
            //eggs=1的时候，肯定是从第0层一直往上实验
            state[1][i] = i;
        }
        //再考虑floors的边界
        for (int i = 1; i <= eggs; i++) {
            //首先是floors=0的情况
            state[i][0] = 0;
            //然后是floors=1的情况
            state[i][1] = 1;
        }

        //第三步就是状态方程了
        //找递推过程中的两个紧邻步骤之间的关系，如何由子结果得到母结果
        //首先，鸡蛋要从2个开始算，因为0个和1个情况你已经考虑完了
        for (int egg = 2; egg <= eggs; egg++) {
            //楼层有多高要从2层起步，因为0层和1层的情况你也考虑完了
            for (int floor = 2; floor <= floors; floor++) {
                //看这里！这里就是你还有egg个鸡蛋，一共有floor层的子问题！
                //这里定义一个变量来存储最终结果，找到在哪层扔能达到所扔次数最少的目标，扔鸡蛋次数多了胳膊会酸！
                int result = Integer.MAX_VALUE;
                for (int drop = 1; drop <= floor; drop++) {
                    //这里！就是在当前子问题中，你从第drop层扔鸡蛋的情况！
                    //第一种情况，哎呀~碎了！那么剩下的问题就转化成了如何在drop-1层，用egg-1个鸡蛋寻找最优解
                    int broken = state[egg - 1][drop - 1];
                    //第二种请看，卧槽~没碎！问题就转化成了如果再floos-drop层，用egg个鸡蛋寻找最优解
                    int unbroken = state[egg][floor - drop];
                    //两种情况我肯定要取最大值，因为我根本不确定鸡蛋会不会碎，我特么又不是先知！
                    int condition = Math.max(broken, unbroken) + 1;
                    //不断的和上一次的结果做比较，只为得到最优的结果，最少的扔鸡蛋次数！
                    result = Math.min(condition, result);
                }
                //当前子问题（当我有egg个鸡蛋，一共有floor层时）已经for循环完了！撒花~~接下来，就是把结果存到我们的结果矩阵里了！
                state[egg][floor] = result;
            }
        }

        //以上的步骤在不断的往状态矩阵（我把它称作装满结果的大盘子！）填充结果！到这里已经都填充完毕，我们自然就可以取到我们想要的结果啦！
        return state[eggs][floors];
    }

    /**
     * 合并两个排序的整数数组A和B变成一个新的数组
     *
     * @param A
     * @param B
     * @return
     */
    public static int[] mergeSortedArray(int[] A, int[] B) {
        //先把两个数组合并成一个数组，然后进行排序
        int[] ab = new int[A.length + B.length];
        System.arraycopy(A, 0, ab, 0, A.length);
        System.arraycopy(B, 0, ab, A.length, B.length);
        Arrays.sort(ab);

        //使用linkList进行处理

        return ab;

    }

    public static void main(String[] args) {
        //两个整数a,b，不使用+号的情况下，计算这两个数字的和
        System.out.println(aplusb(3, 0));

        // 设计一个算法，计算出n阶乘中尾部零的个数
        System.out.println(trailingZeros(5555550000000L));

        //计算两个数组的交集,可重复的
        int[] nums1 = {1, 2, 3, 1};
        int[] nums2 = {2, 3, 1};
        int[] ints = intersection(nums1, nums2);
        for (int i = 0; i < ints.length; i++) {
            System.out.print(ints[i] + " ");
        }

        //计算两个数组的交集,不可重复的
        int[] ints1 = intersectionOnly(nums1, nums2);
        for (int i = 0; i < ints1.length; i++) {
            System.out.print(ints1[i] + " ");
        }

        //左填充,不替换的情况
        System.out.println(leftPad("fod", 5));
        //左填充,替换的情况
        System.out.println(leftPad("fod", 5, '2'));

        //检查两棵二叉树是否等价。
        TreeNode a = new TreeNode(1);
        a.left = new TreeNode(2);
        a.right = new TreeNode(2);
        a.left.left = new TreeNode(4);
        TreeNode b = new TreeNode(1);
        b.left = new TreeNode(2);
        b.right = new TreeNode(2);
        b.left.left = new TreeNode(4);
        System.out.println(isIdentical(a, b));

        //判断字符串是否是有效的括号
        System.out.println(isValidParentheses("[](){"));

        //扔鸡蛋的问题
        System.out.println(dropEggs(10000007));

        //合并两个排序的整数数组A和B变成一个新的数组
        int[] A = {1, 2, 3, 1};
        int[] B = {2, 2, 4};
        for (int i = 0; i < mergeSortedArray(A, B).length; i++) {
            System.out.print(mergeSortedArray(A, B)[i] + " ");
        }

    }
}
