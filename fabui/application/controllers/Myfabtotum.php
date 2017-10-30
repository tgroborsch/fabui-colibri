<?php
/**
 *
 * @author Krios Mane
 * @version 0.1
 * @license https://opensource.org/licenses/GPL-3.0
 *
 */
defined('BASEPATH') OR exit('No direct script access allowed');

class Myfabtotum extends FAB_Controller{
	/**
	 *
	 */
	public function index()
	{
		
	}
	/**
	 * connect to my.fabtotum.com with fabid
	 */
	public function connect($saveToDB = true)
	{
		//load helpers
		$this->load->helper('myfabtotum_helper');
		$this->load->helper('os_helper');
		
		//get data from post
		$fabid    = $this->input->post('fabid_email');
		$password = $this->input->post('fabid_password');
		$serial   = $this->input->post('fabid_serial_number');
		
		$response = array(
				'connect'  => false,
				'register' => false,
				'fabid'    => $fabid
		);
		
		if(isInternetAvaialable()){
			
			$connect  = myfabtotum_connect($fabid, $password); //connect to my.fabtotum.com
			$register = fab_register_printer($fabid, $serial); //register printer
			
			
			$response['register'] = $register;
			$response['connect']  = $connect;
			$response['fabid']    = $fabid;
			
			
			if($saveToDB && $connect['status'] == true){ //save info to user db's record
				
				$this->load->model('User', 'user');
				$this->load->library('session');
				
				$user = $this->user->get($this->session->user['id'], 1);
				
				$user['settings'] = json_decode($user['settings'], true);
				$user['settings']['fabid']['email']    = $fabid;
				$user['settings']['fabid']['password'] = $password;
				$this->session->user = $user;
				$this->user->update($user['id'], array('settings' => json_encode($user['settings'])));
				//reload my.fabtotum.com credentials for the service
				reload_myfabtotum();
			}
		}else{
			$response['connect']['message'] = _("No internet connection found").'<br>'._("Check your connection and try again");
		}
		
		$this->output->set_content_type('application/json')->set_output(json_encode( $response));
	}
	/**
	 * disconnect from my.fabtotum.com
	 */
	function disconnect($fabid = '')
	{
		//load classes
		$this->load->model('User', 'user');
		$this->load->database();
		
		//load helpers
		$this->load->helper('myfabtotum_helper');
		
		if($fabid == ''){
			$this->load->library('session');
			$user = $this->user->get($this->session->user['id'], 1);
		}else{
			$user = $this->user->getByFABID($fabid);
		}
		
		if($user){
			
			$user['settings'] = json_decode($user['settings'], true);
			unset($user['settings']['fabid']);
			
			
			//update user's db record
			$this->user->update($user['id'], array('settings' => json_encode($user['settings'])));
			
			//update session user's info
			if($fabid == ''){
				$this->session->user = $user;
			}
			//reload my.fabtotum.com credentials for the service
			reload_myfabtotum();
		}
		$this->output->set_content_type('application/json')->set_output(json_encode(true));
	}
	/**
	 * return url from my.fabtotum.com
	 */
	public function back_url()
	{
		$fabid = $this->input->get('fabid');
		$data['fabid'] = $fabid;
		
		if($fabid != ''){ //if fabid exists, means login was ok
			
			if(isset($this->session->user)){
				
				//load classes
				$this->load->model('User', 'user');
				//load helpers
				$this->load->helper('myfabtotum_helper');
				
				$user = $this->user->get($this->session->user['id'], 1);
				
				if($user){ //if user exists
					
					$user['settings'] = json_decode($user['settings'], true);
					unset($user['settings']['fabid']);
					$user['settings']['fabid']['email'] = $fabid;
					
					$this->session->user = $user;
					$this->user->update($user['id'], array('settings' => json_encode($user['settings'])));
				}
				
				if(!fab_is_printer_registered()){
					fab_register_printer($fabid);
				}
				
				reload_myfabtotum();	
			}
		}
		
		$this->content = $this->load->view('myfabtotum/back_url', $data, true );
		$this->addJsInLine($this->load->view('myfabtotum/back_url_js', $data, true));
		
		$this->popupLayout();
	}
}
?>
